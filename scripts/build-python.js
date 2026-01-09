const fs = require('fs');
const path = require('path');

const sourceDir = path.resolve(__dirname, '..');
const distDir = path.resolve(sourceDir, 'dist', 'python');
const venvSource = path.resolve(sourceDir, 'venv');
const venvDest = path.resolve(distDir, 'venv');

// Ensure dist/python exists
if (!fs.existsSync(distDir)) {
    fs.mkdirSync(distDir, { recursive: true });
}

// Copy tracker.py
fs.copyFileSync(path.join(sourceDir, 'tracker.py'), path.join(distDir, 'tracker.py'));
console.log('Copied tracker.py');

// Copy venv (simple recursive copy)
function copyFolderSync(from, to) {
    if (!fs.existsSync(to)) fs.mkdirSync(to);
    fs.readdirSync(from).forEach(element => {
        if (element === '__pycache__') return;
        const stat = fs.lstatSync(path.join(from, element));
        if (stat.isFile()) {
            fs.copyFileSync(path.join(from, element), path.join(to, element));
        } else if (stat.isDirectory()) {
            copyFolderSync(path.join(from, element), path.join(to, element));
        }
    });
}

console.log('Copying venv... (this may take a moment)');
copyFolderSync(venvSource, venvDest);
console.log('Copied venv');
