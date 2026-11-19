#!/usr/bin/env python3
"""
Slurm MailProg replacement that emails job notifications over SMTP.

Slurm calls MailProg like /usr/bin/mail:
    mailwrapper.py -s "<subject>" <recipient>

Configure in slurm.conf:
    MailProg=/etc/slurm/mailwrapper.py

Users must give a full email address with --mail-user.
"""

import argparse
import logging
import re
import smtplib
import socket
import subprocess
import sys
import time
from email.message import EmailMessage
from email.utils import formatdate, make_msgid

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SMTP_HOST = "localhost"
SMTP_PORT = 25
SMTP_TIMEOUT = 30

FROM_ADDRESS = "Biocluster <do-not-reply@igb.illinois.edu>"
REPLY_TO = "help@igb.illinois.edu"

LOG_FILE = "/var/log/job.log"
SACCT = "/usr/bin/sacct"
SACCT_DELAY = 10  # seconds to wait for slurmdbd to record the state change
SACCT_FORMAT = ("JobName,NodeList,Partition,User,Account,ExitCode,Timelimit,"
                "NCPUS,NNodes,ReqMem,Submit,Start,End,Elapsed,State,Comment")


def setup_logging():
    handlers = [logging.StreamHandler(sys.stderr)]
    try:
        handlers.append(logging.FileHandler(LOG_FILE))
    except OSError:
        pass
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s mailwrapper[%(process)d] %(levelname)s %(message)s",
        handlers=handlers,
    )


def get_job_id(subject):
    """Parse the job id from the Slurm subject line, which looks like:
        Slurm Job_id=1234 Name=foo Began, Queued time 00:00:01
        Slurm Array Summary Job_id=1234_* (1234) Name=foo Ended, ...
    """
    match = re.search(r"Job_id=(\S+)", subject)
    if not match:
        return None
    job_id = match.group(1)
    # strip "_*" from array summary job ids
    if job_id.endswith("_*"):
        job_id = job_id[:-2]
    return job_id


def run_sacct(job_id, extra_args):
    """Run sacct for a job; return rows (list of lists) or None on failure."""
    cmd = [SACCT, "--jobs=" + job_id, "--parsable2"] + extra_args
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                universal_newlines=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as e:
        logging.error("sacct failed for job %s: %s", job_id, e)
        return None
    if result.returncode != 0:
        logging.error("sacct failed for job %s: %s",
                      job_id, result.stderr.strip())
        return None
    return [line.split("|") for line in result.stdout.splitlines() if line]


def get_job_info(job_id):
    """Allocation-level job details for the main table (with header row)."""
    return run_sacct(job_id, ["--allocations", "--format", SACCT_FORMAT])


# ---------------------------------------------------------------------------
# Resource usage (memory used, CPU efficiency)
# ---------------------------------------------------------------------------
USAGE_FORMAT = "JobID,State,NCPUS,NNodes,ReqMem,TotalCPU,CPUTimeRAW,MaxRSS"
UNFINISHED_STATES = ("PENDING", "RUNNING", "REQUEUED", "RESIZING",
                     "SUSPENDED", "REQUEUE_HOLD", "REQUEUE_FED")
SIZE_UNITS = {"K": 1024, "M": 1024 ** 2, "G": 1024 ** 3,
              "T": 1024 ** 4, "P": 1024 ** 5}


def parse_size(value, default_unit="K"):
    """'1234K', '1.5G', '4000' -> bytes. Returns None if empty/unparseable."""
    value = value.strip()
    if not value:
        return None
    unit = default_unit
    if value[-1].upper() in SIZE_UNITS:
        unit = value[-1].upper()
        value = value[:-1]
    try:
        return float(value) * SIZE_UNITS[unit]
    except ValueError:
        return None


def parse_duration(value):
    """sacct times like '1-02:03:04', '02:03:04', '03:04.567' -> seconds."""
    value = value.strip()
    if not value:
        return None
    try:
        days = 0
        if "-" in value:
            d, value = value.split("-", 1)
            days = int(d)
        parts = [float(p) for p in value.split(":")]
        while len(parts) < 3:
            parts.insert(0, 0.0)
        h, m, s = parts
        return days * 86400 + h * 3600 + m * 60 + s
    except ValueError:
        return None


def requested_mem_bytes(req_mem, ncpus, nnodes):
    """Total requested memory. Slurm 20 suffixes ReqMem with c (per CPU)
    or n (per node); newer Slurm reports the total with no suffix."""
    req_mem = req_mem.strip()
    multiplier = 1
    if req_mem[-1:] == "c":
        multiplier = ncpus
        req_mem = req_mem[:-1]
    elif req_mem[-1:] == "n":
        multiplier = nnodes
        req_mem = req_mem[:-1]
    size = parse_size(req_mem, default_unit="M")
    return size * multiplier if size is not None else None


def human_size(nbytes):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if nbytes < 1024 or unit == "TB":
            return "{:.1f} {}".format(nbytes, unit) if unit != "B" \
                else "{:.0f} B".format(nbytes)
        nbytes /= 1024.0


def human_duration(seconds):
    seconds = int(round(seconds))
    days, rem = divmod(seconds, 86400)
    h, rem = divmod(rem, 3600)
    m, s = divmod(rem, 60)
    text = "{:02d}:{:02d}:{:02d}".format(h, m, s)
    return "{}-{}".format(days, text) if days else text


def get_usage_summary(job_id):
    """Return a text block with memory used and CPU efficiency, or None if
    the job hasn't finished or the data isn't available.

    For array summaries (several allocations), memory is the peak across all
    tasks and CPU efficiency is computed over the whole array.
    """
    rows = run_sacct(job_id, ["--noheader", "--format", USAGE_FORMAT])
    if not rows:
        return None

    allocations, max_rss = [], None
    for row in rows:
        if len(row) < 8:
            continue
        jobid, state, ncpus, nnodes, req_mem, total_cpu, cpu_raw, rss = row[:8]
        if "." in jobid:  # job step: holds the memory usage
            rss_bytes = parse_size(rss)
            if rss_bytes is not None and (max_rss is None or rss_bytes > max_rss):
                max_rss = rss_bytes
        else:
            allocations.append((state, ncpus, nnodes, req_mem,
                                total_cpu, cpu_raw))

    if not allocations:
        return None
    # Only report once the job (or every array task) has finished.
    if any(a[0].split()[0] in UNFINISHED_STATES for a in allocations if a[0]):
        return None

    lines = []

    # Memory: peak RSS of any task vs. memory requested per job/task.
    req_bytes = None
    try:
        a = allocations[0]
        req_bytes = requested_mem_bytes(a[3], int(a[1] or 0), int(a[2] or 0))
    except (ValueError, IndexError):
        pass
    if max_rss is not None:
        line = "Memory used (peak):\t" + human_size(max_rss)
        if req_bytes:
            line += " of {} requested ({:.1f}%)".format(
                human_size(req_bytes), 100.0 * max_rss / req_bytes)
        lines.append(line)

    # CPU efficiency: CPU time used / (cores allocated x elapsed time).
    used = sum(parse_duration(a[4]) or 0 for a in allocations)
    try:
        available = sum(int(a[5] or 0) for a in allocations)
    except ValueError:
        available = 0
    if available > 0:
        lines.append("CPU time used:\t{} of {} core-time".format(
            human_duration(used), human_duration(available)))
        lines.append("CPU efficiency:\t{:.1f}%".format(100.0 * used / available))

    if not lines:
        return None
    note = ("\nLow memory or CPU efficiency means you can request fewer "
            "resources next time,\nwhich usually lets your jobs start sooner.")
    return "Resource usage:\n" + "\n".join(lines) + "\n" + note


def format_table(rows):
    """Transpose sacct output: one line per field, values tab-separated."""
    if not rows:
        return "(no accounting information available)"
    width = max(len(r) for r in rows)
    lines = []
    for col in range(width):
        cells = [r[col] if col < len(r) else "" for r in rows]
        lines.append(":\t".join(cells))
    return "\n".join(lines)


def build_body(job_id, rows, usage=None):
    hostname = socket.gethostname()
    body = ("Biocluster SLURM daemon on {}.\n"
            "Since you requested to be informed by mail, here are some "
            "details of the corresponding job:\n\n\n".format(hostname))
    if rows is None:
        body += ("Job details for job {} could not be retrieved from "
                 "accounting.\n".format(job_id))
    else:
        body += format_table(rows) + "\n"
    if usage:
        body += "\n" + usage + "\n"
    return body


def send_mail(subject, recipients, body):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = FROM_ADDRESS
    msg["To"] = ", ".join(recipients)
    if REPLY_TO:
        msg["Reply-To"] = REPLY_TO
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid()
    msg.set_content(body)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=SMTP_TIMEOUT) as server:
        server.send_message(msg)


def main():
    setup_logging()

    # Mimic /usr/bin/mail's interface: -s <subject> <recipient...>
    parser = argparse.ArgumentParser(description="Slurm MailProg via SMTP")
    parser.add_argument("-s", dest="subject", required=True)
    parser.add_argument("recipients", nargs="+")
    args = parser.parse_args()

    recipients = [r.strip() for r in args.recipients]
    job_id = get_job_id(args.subject)

    rows, usage = None, None
    if job_id:
        time.sleep(SACCT_DELAY)
        rows = get_job_info(job_id)
        try:
            usage = get_usage_summary(job_id)
        except Exception:  # never let usage stats block the notification
            logging.exception("could not compute usage for job %s", job_id)
    else:
        logging.warning("could not determine job id from subject: %s",
                        args.subject)

    body = build_body(job_id, rows, usage)

    try:
        send_mail(args.subject, recipients, body)
    except (smtplib.SMTPException, OSError) as e:
        logging.error("failed to send mail for job %s to %s via %s:%s: %s",
                      job_id, ", ".join(recipients), SMTP_HOST, SMTP_PORT, e)
        return 1

    logging.info("sent '%s' to %s", args.subject, ", ".join(recipients))
    return 0


if __name__ == "__main__":
    sys.exit(main())
