
function make_one(data) {
  //console.log(data);

  row = m_row_start_hover();
  row += make_log("경로", data.foldername);
  row += make_log("파일명", data.filename);
  if (data.filename_pre == null) {
    if (data.result_folder == 'REMOVE') {
      row += make_log('전처리', color("전처리로 삭제"));
    } else {
      row += make_log('전처리', color("전처리로 이동"));
    }
  } else {
    if (data.filename != data.filename_pre) {
      row += make_log("전처리 후 파일명", color(data.filename_pre));
    }
  }

  if (data.filename_pre != null) {
    if (data.entity.filename.is_matched) {
        tmp = data.entity.filename.original_name;
      if (data.entity.filename.original_name != data.entity.filename.name) {
        tmp += ' / 검색용 : ' + color(data.entity.filename.name, 'blue');
      }
      tmp += ' / 회차 : ' + data.entity.filename.no;
      tmp += ' / 날짜 : ' + data.entity.filename.date;
      tmp += ' / 화질 : ' + data.entity.filename.quality;
      tmp += ' / 릴 : ' + data.entity.filename.release;
      tmp += ' / ETC : ' + data.entity.filename.etc;
      tmp += ' / MORE : ' + data.entity.filename.more;
      row += make_log('파일명에서 추출한 정보', tmp);

      tmp = (data.entity.meta.find) ? "매칭" : '<span style="color:red; font-weight:bold">메타 찾지 못함</span>';
      row += make_log('<span style="font-weight:bold">메타 매칭</span>', tmp);
      if (data.entity.meta.find) {
        row += make_log("방송", data.entity.meta.info.title + ' (' + data.entity.meta.info.year + ')' + ' / ' + data.entity.meta.info.code + ' / ' + data.entity.meta.info.genre[0] );
        if ( data.entity.process_info.episode != null) {
          tmp = JSON.stringify(data.entity.process_info.episode, null, 4);
          row += make_log("해당 에피소드 정보", '<pre>' + tmp + '</pre>');

        }
      }
    } else {
      row += make_log('파일명', color('TV 파일 형식이 아님'));
    }

    tmp = data.entity.process_info.status;
    if (tmp != '') {
      if (data.entity.process_info.rebuild != '') {
        tmp += ' / ' + data.entity.process_info.rebuild;
      }
      row += make_log("처리 요약", tmp);
    }
  
  
    row += make_log("최종 경로", data.result_folder);
    if (data.filename == data.result_filename) {
      tmp = '<span style="color:blue; font-weight:bold">' + data.result_filename + '</span>' 
    } else {
      tmp = '<span style="color:red; font-weight:bold">' + data.result_filename + '</span>';
    }
    row += make_log("최종 파일명", tmp);
  }
  row += m_row_end();
  return row
}
