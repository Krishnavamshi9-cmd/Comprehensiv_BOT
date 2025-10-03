import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class ThemeService {
  private darkMode = false;

  constructor() {
    // Check for saved theme preference or default to light mode
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
      this.darkMode = savedTheme === 'dark';
    } else {
      // Check system preference
      this.darkMode = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    }
    this.applyTheme();
  }

  isDarkMode(): boolean {
    return this.darkMode;
  }

  toggleTheme(): void {
    this.darkMode = !this.darkMode;
    this.applyTheme();
    localStorage.setItem('theme', this.darkMode ? 'dark' : 'light');
  }

  setTheme(isDark: boolean): void {
    this.darkMode = isDark;
    this.applyTheme();
    localStorage.setItem('theme', this.darkMode ? 'dark' : 'light');
  }

  private applyTheme(): void {
    if (this.darkMode) {
      document.body.setAttribute('data-theme', 'dark');
    } else {
      document.body.removeAttribute('data-theme');
    }
  }
}
