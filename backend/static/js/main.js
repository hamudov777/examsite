// Таймер экзамена
function startExamTimer(duration, displayId) {
  let timer = duration, minutes, seconds;
  const display = document.getElementById(displayId);
  const interval = setInterval(function () {
    minutes = Math.floor(timer / 60);
    seconds = timer % 60;
    display.textContent = `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
    if (--timer < 0) {
      clearInterval(interval);
      display.textContent = "Время вышло!";
      // Автоматическая отправка формы/экзамена
      document.getElementById('exam-form').submit();
    }
  }, 1000);
}

// Сохранение темы между вкладками/страницами и синхронизация с html
document.addEventListener('DOMContentLoaded', function() {
  // Установить тему, если выбрана ранее
  if (localStorage.getItem('theme') === 'dark') {
    document.documentElement.classList.add('dark');
  } else {
    document.documentElement.classList.remove('dark');
  }

  const btn = document.getElementById('theme-toggle');
  if (btn) {
    btn.onclick = () => {
      const isDark = document.documentElement.classList.toggle('dark');
      localStorage.setItem('theme', isDark ? 'dark' : 'light');
    };
  }

  // Синхронизация между вкладками
  window.addEventListener('storage', function(e) {
    if (e.key === 'theme') {
      if (e.newValue === 'dark') {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
    }
  });
});

// Поиск по экзаменам и тестам
document.addEventListener('DOMContentLoaded', function() {
  const searchInput = document.getElementById('search-input');
  const examsList = document.getElementById('exams-list');
  const testsList = document.getElementById('tests-list');

  if (searchInput && examsList && testsList) {
    searchInput.addEventListener('input', function() {
      const value = this.value.trim().toLowerCase();
      // Фильтрация экзаменов
      Array.from(examsList.getElementsByClassName('exam-card')).forEach(card => {
        const title = card.getAttribute('data-title') || '';
        card.style.display = title.includes(value) ? '' : 'none';
      });
      // Фильтрация тестов
      Array.from(testsList.getElementsByClassName('exam-card')).forEach(card => {
        const title = card.getAttribute('data-title') || '';
        card.style.display = title.includes(value) ? '' : 'none';
      });
    });
  }
});