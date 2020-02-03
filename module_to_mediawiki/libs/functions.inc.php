<?php

function send_curl($website,$post_array,$cookie) {

        $post_string = http_build_query($post_array);
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL,$website);
        curl_setopt($ch, CURLOPT_POSTFIELDS,$post_string);
        curl_setopt($ch, CURLOPT_POST, 1);
        curl_setopt($ch, CURLOPT_COOKIEJAR, $cookie);
        curl_setopt($ch, CURLOPT_COOKIEFILE, $cookie);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
        $result = json_decode(curl_exec($ch),true);
        curl_close($ch); // curl closed
        return $result;



}
function wiki_login($website_api,$username,$password,$domain,$cookie_file) {
        $format = 'json';
        $post_query = array('action'=>'query',
		'meta'=>'tokens',
		'type'=>'login',
                'format'=>$format);

        $token_result = send_curl($website_api,$post_query,$cookie_file);
        if (isset($token_result['query']['tokens']['logintoken'])) {

                $post_query_confirm = array('action'=>'login',
                                'lgname'=>$username,
                                'lgpassword'=>$password,
                                'lgdomain'=>$domain,
                                'format'=>$format,
                                'lgtoken'=>$token_result['query']['tokens']['logintoken']);
                $login_result = send_curl($website_api,$post_query_confirm,$cookie_file);
		if ($login_result['login']['result'] == 'Success') {
	                return $token_result['query']['tokens']['logintoken'];
		}
        }
        return false;
}

function wiki_edit_token($website_api,$cookie_file) {
        $format = 'json';
        $post_query = array('action'=>'query',
                'meta'=>'tokens',
		'type'=>'csrf',
		'format'=>$format,
                );
        $result = send_curl($website_api,$post_query,$cookie_file);
	if (isset($result['query']['tokens']['csrftoken'])) {
        	return $result['query']['tokens']['csrftoken'];
	}
	return false;


}
function wiki_edit_page($website_api,$title,$text,$cookie_file) {
        $edit_token = wiki_edit_token($website_api,$cookie_file);
        $format = 'json';
        $post_query = array('action'=>'edit',
                        'format'=>'json',
                        'title'=>$title,
                        'text'=>$text,
                        'contentformat','text/x-wiki',
                        'token'=>$edit_token);
        $result = send_curl($website_api,$post_query,$cookie_file);
        if (isset($result['edit']['result']) && ($result['edit']['result'] == 'Success')) {
                return true;
        }
        return false;

}


function get_lmod_apps($directory) {

	if (file_exists($directory)) {
		$exec = "source /etc/profile; " . __LMOD_SPIDER_PATH__ . " -o jsonSoftwarePage " . $directory;
		$exit_status = 1;
		$output_array = array();
		$output = exec($exec,$output_array,$exit_status);
		if (!$exit_status) {
			$result = json_decode($output,true);
	        	if (!json_last_error()) {
		                return $result;
			}
	        }
	}
	return false;

}


function log_alert($message) {
	$current_time = date('Y-m-d H:i:s');
	$full_msg = $current_time . ": " . $message . "\n";
		
	if (php_sapi_name() == "cli") {
		echo $full_msg;
	}

}

function get_ignore_apps() {
	//$ignore_apps = array();
	//if (isset(__IGNORE_APPS__) {
		$ignore_apps = explode(" ",__IGNORE_APPS__);
	//}
	return $ignore_apps;
}
?>
