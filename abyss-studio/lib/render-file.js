import fs from 'node:fs';
import path from 'node:path';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {root} from './config.js';

const libraries = [
  ['/production/episodes/', path.join(root,'production/episodes')],
  ['/factory/',path.resolve(root,'../codex-video-factory/production')]
];

export async function renderFile(input) {
  const url = input.file;
  const library = typeof url === 'string' && libraries.find(([prefix])=>url.startsWith(prefix));
  if (!library || !['path','reveal'].includes(input.action)) throw Error('Chọn một bản MP4 trong xưởng.');
  const [prefix,base] = library;
  const parts = decodeURIComponent(url.slice(prefix.length)).split('/');
  if (parts.some(s=>!s || s.startsWith('.') || /[\\:\x00-\x1f]/.test(s)) || !/\.mp4$/i.test(parts.at(-1)))
    throw Error('Đường dẫn MP4 không hợp lệ.');
  const directory = fs.realpathSync(base);
  const candidate = path.join(directory,...parts);
  const file = fs.existsSync(candidate) && fs.realpathSync(candidate);
  if (!file || !file.startsWith(directory+path.sep) || !fs.statSync(file).isFile())
    throw Error('Không tìm thấy bản render trong thư mục tập.');
  if (input.action === 'reveal') {
    // Resolve the item to a shell ID and wait for Windows to accept the selection.
    const select = 'import sys; from win32com.shell import shell; item=shell.SHILCreateFromPath(sys.argv[1],0)[0]; shell.SHOpenFolderAndSelectItems(item[:-1],[item[-1:]],0)';
    try {
      await promisify(execFile)('python',['-X','utf8','-c',select,file],{windowsHide:true,timeout:12000});
    } catch { throw Error('Windows chưa mở được thư mục. Dùng nút Chép đường dẫn MP4.'); }
  }
  return {path:file};
}
