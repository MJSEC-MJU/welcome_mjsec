const express = require('express');
const path = require('path');
const fs = require('fs');
const cors = require('cors');


const app = express();
const PORT = 8000;

// 미들웨어 설정
app.use(cors());
app.use(express.json());

// JSON 파싱 실패 시 400.html 반환
app.use((err, req, res, next) => {
  if (err instanceof SyntaxError && err.status === 400 && 'body' in err) {
    console.error('JSON 파싱 오류:', err.message);
    return res.status(400).sendFile(path.join(__dirname, 'errors', '400.html'));
  }
  next();
});

// 정답(차례대로 400, 403, 404)
const correctAnswers = ['MJSEC{VmtaV2QxWkdTbFpWU0U1elRsVkZPUT09}', 'MJSEC{VGpCd2NHRjZaRXBrVjJNeVkydGpNQT09}', 'MJSEC{N1ptWTdKaUI3WldwNjR1STY0dWtJUT09}'];

// public만 노출
app.use(express.json());
app.use(express.static('public'));

// /admin 및 /admin.html 접근 시도 시 차단
app.get(['/admin', '/admin.html'], (req, res) => {
  res.status(403).sendFile(path.join(__dirname, 'errors', '403.html'));
});

// 서버 내부 전용 admin.html 보기
app.get('/show-admin', (req, res) => {
  try {
    const adminHtml = fs.readFileSync(path.join(__dirname, 'private', 'admin.html'), 'utf8');
    res.send(adminHtml);
  } catch (err) {
    console.error('admin.html 읽기 실패:', err);
    res.status(500).send('서버 오류');
  }
});

// 정답 확인
app.post('/check', (req, res) => {
  const { answer1, answer2, answer3 } = req.body;

  // 입력 누락
  if (!answer1 || !answer2 || !answer3) {
    return res.status(200).json({ success: false, message: '정답을 모두 입력하세요.' });
  }

  // 정답 확인
  if (
    answer1 === correctAnswers[0] &&
    answer2 === correctAnswers[1] &&
    answer3 === correctAnswers[2]
  ) {
    return res.json({ success: true, message: '🎉 정답입니다! 플래그는 MJSEC{VFVwVFJVUHNsNUFnN0ppazdJdWc2ckc0SU8yWm1PeVlnZTJWcWV1TGlPdUxwQ0U9} 입니다.\n{}안의 플래그를 base64 디코딩 해보세요!' });
  }

  // 정답 틀림
  return res.status(200).json({ success: false, message: '정답이 틀렸습니다. 다시 시도하세요.' });
});
// 존재하지 않는 경로 요청 시 404.html 반환
app.use((req, res) => {
  res.status(404).sendFile(path.join(__dirname, 'errors', '404.html'));
});

app.listen(PORT, () => {
  console.log(`서버 실행 중: http://localhost:${PORT}`);
});
