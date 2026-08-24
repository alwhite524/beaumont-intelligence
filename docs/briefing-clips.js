(() => {
  const toSeconds = value => {
    const parts = value.split(':').map(Number);
    if (parts.some(Number.isNaN) || parts.length < 2 || parts.length > 3) return null;
    return parts.reduce((total, part) => total * 60 + part, 0);
  };
  const fromSeconds = value => {
    const hours = Math.floor(value / 3600);
    const minutes = Math.floor((value % 3600) / 60);
    const seconds = value % 60;
    return hours ? `${hours}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}` : `${minutes}:${String(seconds).padStart(2, '0')}`;
  };
  const meetingVideo = [...document.querySelectorAll('a[href*="youtube.com/watch"]')].map(link => {
    try { return new URL(link.href).searchParams.get('v'); } catch { return null; }
  }).find(Boolean);
  if (!meetingVideo) return;

  document.querySelectorAll('.agenda-item .after-grid').forEach(summary => {
    const videoValue = [...summary.querySelectorAll('div')].find(item => item.querySelector('strong')?.textContent.trim() === 'Video')?.querySelector('span');
    if (!videoValue || videoValue.querySelector('a')) return;
    const match = videoValue.textContent.match(/(\d{1,2}:\d{2}(?::\d{2})?)\s*[·–-]\s*Vote\s+(\d{1,2}:\d{2}(?::\d{2})?)/i);
    if (!match) return;
    const start = toSeconds(match[1]);
    const vote = toSeconds(match[2]);
    if (start === null || vote === null || vote < start) return;

    const end = vote + 15;
    const item = summary.closest('.agenda-item');
    const title = item?.querySelector('h3')?.textContent.trim() || 'Council discussion';
    const params = new URLSearchParams({
      video: meetingVideo,
      start: String(start),
      end: String(end),
      title,
      range: `${match[1]}–${fromSeconds(end)}`,
      return: `${location.pathname.split('/').pop()}#${item?.id || ''}`
    });
    videoValue.innerHTML = `<a href="video-viewer.html?${params}">${match[1]}–${fromSeconds(end)} →</a>`;
  });
})();
