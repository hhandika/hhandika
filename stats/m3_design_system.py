"""Material 3 design system constants and styles."""


class M3Tokens:
    """Contains Material 3 CSS tokens for light and dark modes."""

    # Fonts
    FONTS = "font-family: 'Roboto', 'Google Sans', system-ui, sans-serif;"

    # CSS variables definition
    CSS_VARIABLES = """
    :root {
      /* Light Theme (Chetwode & Porsche) */
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
        /* Dark Theme (Chetwode & Porsche) */
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
      rx: 24px;
      fill: var(--md-sys-color-surface);
      stroke: var(--md-sys-color-outline-variant);
      stroke-width: 1px;
    }
    .m3-card-medium {
      rx: 16px;
      fill: var(--md-sys-color-surface-container);
      stroke: var(--md-sys-color-outline-variant);
      stroke-width: 0.5px;
    }
    .m3-bar-chart {
      rx: 4px;
    }
    .m3-divider {
      stroke: var(--md-sys-color-outline-variant);
      stroke-width: 1px;
      opacity: 0.5;
    }
    """

    @classmethod
    def get_style_block(cls) -> str:
        """Returns the full style block for the SVG."""
        return f"<style>\\n{cls.CSS_VARIABLES}\\n{cls.TYPOGRAPHY}\\n{cls.SHAPES}\\n</style>"
