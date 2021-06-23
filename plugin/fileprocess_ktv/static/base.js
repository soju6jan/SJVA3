function make_log(key, value) {
  row = m_col(2, key, aligh='right');
  row += m_col(10, value, aligh='left');
  return row;
}

function color(text, color='red') {
  return '<span style="color:'+color+'; font-weight:bold">' + text + '</span>';
}

$("body").on('click', '#dry_run_start_btn', function(e){
  e.preventDefault();
  global_send_command2('dry_run_start');
});
  
$("body").on('click', '#dry_run_stop_btn', function(e){
  e.preventDefault();
  global_send_command2('dry_run_stop');
});

function socket_init(package_name, sub) {
  socket = io.connect(window.location.protocol + "//" + document.domain + ":" + location.port + "/" + package_name + '/' + sub);

  socket.on('start', function(data){
    global_send_command2('refresh');
  });

  socket.on('refresh_all', function(data){
    console.log(data)
    make_list(data);
  });

  socket.on('refresh_one', function(data){
    console.log(data)
    row = make_one(data);
    id = 'data_'+data.index;
    if ($('#' + id).length) {
      $('#' + id).html(row);
      current_data.data[parseInt(data.index)] = data;
    } else {
      row = '<div id="' + id + '">' + row + '</div>';
      document.getElementById("list_div").innerHTML += m_hr() + row;
      current_data.data.push(data);
      //[parseInt(data.index)] = data;
    }
    
  });
}


function make_list(data2) {
  current_data = data2;
  str = '';
  if (data2.is_working == 'run')  tmp = '실행중';
  else if (data2.is_working == 'wait')  tmp = '대기';
  else if (data2.is_working == 'stop')  tmp = '사용자 중지';
  str += '<br><h4>상태 : ' + tmp + '</h4>'
  data = data2.data;
  // if (data == null || data.length == 0) str += '<br><h4>목록이 없습니다.</h4>'
  for (i in data) {
    str += m_hr();
    str += '<div id="data_' + data[i].index + '">';
    str += make_one(data[i]);
    str += '</div>';
   
  }
  document.getElementById("list_div").innerHTML = str;
}

