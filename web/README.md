public/submit.obfuscated.js 난독화 안된버전


function submitAnswers() {
    const ans1 = document.getElementById('answer1').value;
    const ans2 = document.getElementById('answer2').value;
    const ans3 = document.getElementById('answer3').value;
  
    fetch('/check', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ answer1: ans1, answer2: ans2, answer3: ans3 })
    })
    .then(res => {
      if (!res.ok) {
        if ([400, 403, 404].includes(res.status)) {
          return res.text().then(html => {
            document.documentElement.innerHTML = html;
          });
        } else {
          throw new Error('서버 오류');
        }
      }
  
      return res.json();
    })
    .then(data => {
      if (!data) return;
  
      if (data.success) {
        document.getElementById('result').innerHTML = `<a href="${data.link}">링크로 이동하기</a>`;
      } else {
        document.getElementById('result').innerText = data.message;
      }
    })
    .catch(err => {
      console.error('예외 발생:', err);
      fetch('/errors/500.html')
        .then(res => res.text())
        .then(html => {
          document.documentElement.innerHTML = html;
        });
    });
  }
