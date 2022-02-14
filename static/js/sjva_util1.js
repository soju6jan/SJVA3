///////////////////////////////////////////////////////////////////////////////
// Util  JS 파일로 뺄것
///////////////////////////////////////////////////////////////////////////////

function humanFileSize(bytes) {
  var thresh = 1024;
  if(Math.abs(bytes) < thresh) {
      return bytes + ' B';
  }
  var units = ['KB','MB','GB','TB','PB','EB','ZB','YB']
  var u = -1;
  do {
      bytes /= thresh;
      ++u;
  } while(Math.abs(bytes) >= thresh && u < units.length - 1);
  return bytes.toFixed(1)+' '+units[u];
}

function FormatNumberLength(num, length) {
  var r = "" + num;
  while (r.length < length) {
      r = "0" + r;
  }
  return r;
}

function msToHMS( ms ) {
  // 1- Convert to seconds:
  var seconds = ms / 1000;
  // 2- Extract hours:
  var hours = parseInt( seconds / 3600 ); // 3,600 seconds in 1 hour
  seconds = seconds % 3600; // seconds remaining after extracting hours
  // 3- Extract minutes:
  var minutes = parseInt( seconds / 60 ); // 60 seconds in 1 minute
  // 4- Keep only seconds not extracted to minutes:
  seconds = seconds % 60;
  return (''+hours).padStart(2, "0")+":"+(''+minutes).padStart(2, "0")+":"+parseInt(seconds);
}


function color(text, color='red') {
  return '<span style="color:'+color+'; font-weight:bold">' + text + '</span>';
}



function text_color(text, color='red') {
  return '<span style="color:'+color+'; font-weight:bold">' + text + '</span>';
}


function make_log(key, value, left=2, right=10) {
  row = m_col(left, key, aligh='right');
  row += m_col(right, value, aligh='left');
  return row;
}