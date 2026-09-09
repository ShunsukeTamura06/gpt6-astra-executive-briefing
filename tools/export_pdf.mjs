// exec_ai_briefing.html から exec_ai_briefing_backup.pdf を書き出す。
// カウントアップ数字・ファネル図はIntersectionObserver依存で印刷時に発火しないため、
// 強制的に最終値へセットしてから出力する（.dataset.counted='1' で再発火もガード）。
// 実行: node tools/export_pdf.mjs （プロジェクトルートから）
import { chromium } from 'playwright';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, '..');

const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';

const b = await chromium.launch({ executablePath: CHROME });
const p = await b.newPage();
await p.goto('file://' + path.join(root, 'exec_ai_briefing.html'));
await p.emulateMedia({ media: 'print' });

await p.evaluate(() => {
  document.querySelectorAll('[data-count-to]').forEach((el) => {
    const dec = parseInt(el.getAttribute('data-decimals') || '0', 10);
    el.textContent = parseFloat(el.getAttribute('data-count-to')).toFixed(dec);
    el.dataset.counted = '1';
  });
});
await p.waitForTimeout(1200);

await p.pdf({
  path: path.join(root, 'exec_ai_briefing_backup.pdf'),
  width: '1600px',
  height: '900px',
  printBackground: true,
  margin: { top: '0', bottom: '0', left: '0', right: '0' },
});
await b.close();
console.log('pdf ok ->', path.join(root, 'exec_ai_briefing_backup.pdf'));
