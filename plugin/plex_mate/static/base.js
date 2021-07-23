function make_log(key, value) {
  row = m_col(2, key, aligh='right');
  row += m_col(10, value, aligh='left');
  return row;
}

function color(text, color='red') {
  return '<span style="color:'+color+'; font-weight:bold">' + text + '</span>';
}


function socket_init(package_name, sub, sub2) {
  socket = io.connect(window.location.protocol + "//" + document.domain + ":" + location.port + "/" + package_name + '/' + sub + '/' + sub2);

  socket.on('start', function(data){
    global_send_command_sub('refresh');
  });

  socket.on('refresh_all', function(data){
      make_list(data);
      make_status(data.status);
  });

  socket.on('refresh_one', function(data){
    row = make_one(data.one);
    make_status(data.status);
    id = 'data_'+data.one.index;
    if ($('#' + id).length) {
      $('#' + id).html(row);
      current_data.list[parseInt(data.one.index)] = data.one;
    } else {
      row = '<div id="' + id + '">' + row + '</div>';
      document.getElementById("list_div").innerHTML += m_hr() + row;
      if (current_data == null)
          current_data = []
      if (current_data.list == null)
          current_data.list = []
      current_data.list.push(data.one);
      //[parseInt(data.index)] = data;
    }
  });
}



function make_list(data2) {
  current_data = data2;
  
  data = data2.list;
  str = '';
  // if (data == null || data.length == 0) str += '<br><h4>목록이 없습니다.</h4>'
  for (i in data) {
    
    str += '<div id="data_' + data[i].index + '">';
    str += make_one(data[i]);
    str += '</div>';
    str += m_hr();
    
  }
  document.getElementById("list_div").innerHTML = str;
}

