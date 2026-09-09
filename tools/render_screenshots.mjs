// 全スライドをPNGでスクリーンショット。レイアウト崩れ・動画再生・アニメーションの
// 目視確認に使う。実行: node tools/render_screenshots.mjs （プロジェクトルートから）
import { chromium } from 'playwright';
import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, '..');
const outDir = path.join(root, 'tools', '_screenshots');
fs.mkdirSync(outDir, { recursive: true });

const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';

const b = await chromium.launch({ executablePath: CHROME });
const p = await b.newPage({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 1 });
await p.goto('file://' + path.join(root, 'exec_ai_briefing.html'));
await p.waitForTimeout(600);

const n = await p.locator('section').count();
for (let i = 0; i < n; i++) {
  await p.evaluate(
    (idx) => document.querySelectorAll('section')[idx].scrollIntoView({ behavior: 'instant', block: 'start' }),
    i
  );
  await p.waitForTimeout(1500); // 動画のオートプレイ・カウントアップ・ファネル演出が落ち着くのを待つ
  await p.screenshot({ path: path.join(outDir, `s${String(i).padStart(2, '0')}.png`) });
}
console.log('sections:', n, '-> saved to', outDir);
await b.close();
