"""Material 3 design system constants and styles."""


class M3Tokens:
    """Contains Material 3 CSS tokens for light and dark modes."""

    # Fonts
    FONTS = "font-family: 'Roboto', 'Google Sans', system-ui, sans-serif;"

    # CSS variables definition
    CSS_VARIABLES = """
    :root {
      /* Light Theme (Chetwode and Porsche) */
      --md-sys-color-surface: #fcfcfc;
      --md-sys-color-on-surface: #1a1c1e;
      --md-sys-color-surface-variant: #e1e2e8;
      --md-sys-color-on-surface-variant: #44474e;
      --md-sys-color-surface-container: #f0f5fd; /* Chetwode 50 */
      
      --md-sys-color-primary: #5a67d1; /* Chetwode 600 */
      --md-sys-color-on-primary: #ffffff;
      --md-sys-color-primary-container: #e4edfb; /* Chetwode 100 */
      --md-sys-color-on-primary-container: #384077; /* Chetwode 900 */
      
      --md-sys-color-tertiary: #c46f32; /* Porsche 600 */
      --md-sys-color-on-tertiary: #ffffff;
      --md-sys-color-tertiary-container: #f8eedc; /* Porsche 100 */
      --md-sys-color-on-tertiary-container: #6a3b24; /* Porsche 900 */
      
      --md-sys-color-outline: #74777f;
      --md-sys-color-outline-variant: #c4c7c5;
    }
    
    @media (prefers-color-scheme: dark) {
      :root {
        /* Dark Theme (Chetwode and Porsche) */
        --md-sys-color-surface: #1a1c1e;
        --md-sys-color-on-surface: #e2e2e6;
        --md-sys-color-surface-variant: #44474e;
        --md-sys-color-on-surface-variant: #c4c6d0;
        --md-sys-color-surface-container: #212545; /* Chetwode 950 */
        
        --md-sys-color-primary: #b0c6f1; /* Chetwode 300 */
        --md-sys-color-on-primary: #3e4795; /* Chetwode 800 */
        --md-sys-color-primary-container: #4a54b8; /* Chetwode 700 */
        --md-sys-color-on-primary-container: #e4edfb; /* Chetwode 100 */
        
        --md-sys-color-tertiary: #e5bf8c; /* Porsche 300 */
        --md-sys-color-on-tertiary: #82462a; /* Porsche 800 */
        --md-sys-color-tertiary-container: #a2572c; /* Porsche 700 */
        --md-sys-color-on-tertiary-container: #f8eedc; /* Porsche 100 */
        
        --md-sys-color-outline: #8e9099;
        --md-sys-color-outline-variant: #444746;
      }
    }
    """

    TYPOGRAPHY = (
        """
    .m3-headline-small {
      """
        + FONTS
        + """
      font-size: 24px;
      font-weight: 400;
      line-height: 32px;
      fill: var(--md-sys-color-on-surface);
    }
    .m3-title-medium {
      """
        + FONTS
        + """
      font-size: 16px;
      font-weight: 500;
      line-height: 24px;
      letter-spacing: 0.15px;
      fill: var(--md-sys-color-on-surface);
    }
    .m3-title-small {
      """
        + FONTS
        + """
      font-size: 14px;
      font-weight: 500;
      line-height: 20px;
      letter-spacing: 0.1px;
      fill: var(--md-sys-color-on-surface);
    }
    .m3-body-large {
      """
        + FONTS
        + """
      font-size: 16px;
      font-weight: 400;
      line-height: 24px;
      letter-spacing: 0.5px;
      fill: var(--md-sys-color-on-surface-variant);
    }
    .m3-body-medium {
      """
        + FONTS
        + """
      font-size: 14px;
      font-weight: 400;
      line-height: 20px;
      letter-spacing: 0.25px;
      fill: var(--md-sys-color-on-surface-variant);
    }
    .m3-body-small {
      """
        + FONTS
        + """
      font-size: 12px;
      font-weight: 400;
      line-height: 16px;
      letter-spacing: 0.4px;
      fill: var(--md-sys-color-on-surface-variant);
    }
    .m3-label-large {
      """
        + FONTS
        + """
      font-size: 14px;
      font-weight: 500;
      line-height: 20px;
      letter-spacing: 0.1px;
      fill: var(--md-sys-color-primary);
    }
    .m3-label-medium {
      """
        + FONTS
        + """
      font-size: 12px;
      font-weight: 500;
      line-height: 16px;
      letter-spacing: 0.5px;
      fill: var(--md-sys-color-on-surface-variant);
    }
    .m3-display-small {
      """
        + FONTS
        + """
      font-size: 36px;
      font-weight: 400;
      line-height: 44px;
      fill: var(--md-sys-color-on-surface);
    }
    """
    )

    SHAPES = """
    .m3-container-large {
      rx: 12px;
      fill: var(--md-sys-color-surface);
      stroke: var(--md-sys-color-outline-variant);
      stroke-width: 1px;
    }
    .m3-card-medium {
      rx: 8px;
      fill: var(--md-sys-color-surface-container);
      stroke: var(--md-sys-color-outline-variant);
      stroke-width: 0.5px;
    }
    .m3-bar-chart {
      rx: 2px;
    }
    .m3-divider {
      stroke: var(--md-sys-color-outline-variant);
      stroke-width: 1px;
      opacity: 0.5;
    }
    """

    ICONS = {
        "stars": "M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z",
        "contributions": "M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zm6.93 6h-2.95a15.65 15.65 0 00-1.38-3.56A8.03 8.03 0 0118.92 8zM12 4.04c.83 1.2 1.48 2.53 1.91 3.96h-3.82c.43-1.43 1.08-2.76 1.91-3.96zM4.26 14C4.1 13.36 4 12.69 4 12s.1-1.36.26-2h3.38c-.08.66-.14 1.32-.14 2s.06 1.34.14 2H4.26zm.82 2h2.95c.32 1.25.78 2.45 1.38 3.56A7.987 7.987 0 015.08 16zm2.95-8H5.08a7.987 7.987 0 014.33-3.56C8.81 5.55 8.35 6.75 8.03 8zM12 19.96c-.83-1.2-1.48-2.53-1.91-3.96h3.82c-.43 1.43-1.08 2.76-1.91 3.96zM14.34 14H9.66c-.09-.66-.16-1.32-.16-2s.07-1.35.16-2h4.68c.09.65.16 1.32.16 2s-.07 1.34-.16 2zm1.15 5.56c.6-1.11 1.06-2.31 1.38-3.56h2.95a8.03 8.03 0 01-4.33 3.56zM16.24 14c.08-.66.14-1.32.14-2s-.06-1.34-.14-2h3.38c.16.64.26 1.31.26 2s-.1 1.36-.26 2h-3.38z",
        "prs": "M17 20.24c1.32 0 2.4-1.08 2.4-2.4s-1.08-2.4-2.4-2.4-2.4 1.08-2.4 2.4 1.08 2.4 2.4 2.4zM17 17c.46 0 .84.38.84.84s-.38.84-.84.84-.84-.38-.84-.84.38-.84.84-.84zM7 8.56c1.32 0 2.4-1.08 2.4-2.4S8.32 3.76 7 3.76 4.6 4.84 4.6 6.16s1.08 2.4 2.4 2.4zm0-3.24c.46 0 .84.38.84.84s-.38.84-.84.84-.84-.38-.84-.84.38-.84.84-.84zM7 20.24c1.32 0 2.4-1.08 2.4-2.4s-1.08-2.4-2.4-2.4-2.4 1.08-2.4 2.4 1.08 2.4 2.4 2.4zm0-3.24c.46 0 .84.38.84.84s-.38.84-.84.84-.84-.38-.84-.84.38-.84.84-.84zM8 9.3v5.14c0 .88.72 1.6 1.6 1.6h5.84c.3-.5.78-.86 1.34-1l-5.58-.01c-.33 0-.6-.27-.6-.6V9.3c.56-.14 1.04-.5 1.34-1H9.34C9.04 8.8 8.56 9.16 8 9.3zM17 3.76c-1.32 0-2.4 1.08-2.4 2.4s1.08 2.4 2.4 2.4 2.4-1.08 2.4-2.4-1.08-2.4-2.4-2.4zm0 3.24c-.46 0-.84-.38-.84-.84s.38-.84.84-.84.84.38.84.84-.38.84-.84.84zM16.2 8.3h1.6v6.62h-1.6z",
        "reviews": "M20 2H4c-1.1 0-1.99.9-1.99 2L2 22l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zM6 14v-2.47l6.88-6.88c.2-.2.51-.2.71 0l1.77 1.77c.2.2.2.51 0 .71L8.47 14H6zm12 0h-7.5l2-2H18v2z",
        "issues": "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z",
        "reuse": "M12 1.5l3.53 3.53L12 8.56V5.5C7.31 5.5 3.5 9.31 3.5 14s3.81 8.5 8.5 8.5c2.32 0 4.41-.93 5.95-2.45l1.41 1.41C17.47 23.36 14.88 24.5 12 24.5c-5.8 0-10.5-4.7-10.5-10.5S6.2 3.5 12 3.5V1.5zm6.5 12.5c0-1.66-.66-3.17-1.74-4.26l-1.41 1.41c.65.65 1.15 1.55 1.15 2.85 0 2.21-1.79 4-4 4v3l-3.53-3.53L12.5 14v3c3.31 0 6-2.69 6-6z",
        "streak": "M11.71 2.53C11.52 2.19 11 2.37 11 2.76c0 .88-.36 3.65-2.52 5.81-1.99 1.99-2.52 3.63-2.52 5.09 0 3.32 2.68 6 6 6s6-2.68 6-6c0-1.46-.53-3.1-2.52-5.09-2.16-2.16-2.52-4.93-2.52-5.81 0-.39-.52-.57-.71-.23-.88 1.53-3.37 5.06-1.5 8.01-1.39-1.22-1.98-3.03-1.5-4.63zM12 17c-1.66 0-3-1.34-3-3 0-1.34 1.34-3.34 3-5.02 1.66 1.68 3 3.68 3 5.02 0 1.66-1.34 3-3 3z",
        "peak_day": "M19 3h-1V1h-2v2H8V1H6v2H5c-1.11 0-1.99.9-1.99 2L3 19c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V8h14v11z",
        "peak_hours": "M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67z",
    }

    @classmethod
    def get_style_block(cls) -> str:
        """Returns the full style block for the SVG."""
        return f"<style>\n{cls.CSS_VARIABLES}\n{cls.TYPOGRAPHY}\n{cls.SHAPES}\n</style>"
