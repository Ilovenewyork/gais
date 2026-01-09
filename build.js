const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Configuration
const config = {
  distDir: path.join(__dirname, 'dist'),
  buildDir: path.join(__dirname, 'build'),
  pythonDistDir: path.join(__dirname, 'dist', 'python'),
  pythonExeName: 'tracker',
  electronDistDir: path.join(__dirname, 'dist', 'electron')
};

// Create necessary directories
function createDirectories() {
  [config.distDir, config.buildDir, config.pythonDistDir, config.electronDistDir].forEach(dir => {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
  });
}

// Build Python executable using the spec file
function buildPython() {
  console.log('Building Python executable...');
  try {
    execSync(`pyinstaller --clean --noconfirm tracker.spec`, { 
      stdio: 'inherit',
      cwd: __dirname
    });

    // The output should be in the dist directory
    const sourceFile = path.join(__dirname, 'dist', 'tracker.exe');
    const destFile = path.join(config.pythonDistDir, `${config.pythonExeName}.exe`);
    
    if (fs.existsSync(sourceFile)) {
      // Ensure destination directory exists
      if (!fs.existsSync(path.dirname(destFile))) {
        fs.mkdirSync(path.dirname(destFile), { recursive: true });
      }
      
      // Copy the file instead of moving in case we need to rebuild
      fs.copyFileSync(sourceFile, destFile);
      console.log(`Python executable built successfully at ${destFile}`);
      return true;
    } else {
      console.error(`Error: Python executable not found at ${sourceFile}`);
      return false;
    }
  } catch (error) {
    console.error('Error building Python executable:', error);
    return false;
  }
}

// Main build function
async function build() {
  console.log('Starting build process...');
  
  // Create necessary directories
  createDirectories();
  
  // Build Python executable
  const pythonBuilt = buildPython();
  if (!pythonBuilt) {
    console.error('Failed to build Python executable. Exiting...');
    process.exit(1);
  }
  
  console.log('Build process completed successfully!');
  console.log(`Python executable is available at: ${path.join(config.pythonDistDir, `${config.pythonExeName}.exe`)}`);
}

// Run the build
build().catch(err => {
  console.error('Build failed:', err);
  process.exit(1);
});
