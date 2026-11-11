let initialTheme;
let savedTheme = localStorage.getItem('theme');
if (savedTheme) {
  initialTheme = savedTheme;
} else {
  if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
    initialTheme = 'dark';
  } else {
    initialTheme = 'light';
  }
}
document.documentElement.setAttribute('data-theme', initialTheme);
