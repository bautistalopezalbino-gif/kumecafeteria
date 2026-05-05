---
name: KÜME café
colors:
  surface: '#fcf9f8'
  surface-dim: '#dcd9d9'
  surface-bright: '#fcf9f8'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f6f3f2'
  surface-container: '#f0eded'
  surface-container-high: '#eae7e7'
  surface-container-highest: '#e5e2e1'
  on-surface: '#1c1b1b'
  on-surface-variant: '#444840'
  inverse-surface: '#313030'
  inverse-on-surface: '#f3f0ef'
  outline: '#75786f'
  outline-variant: '#c5c8bd'
  surface-tint: '#536345'
  primary: '#536345'
  on-primary: '#ffffff'
  primary-container: '#6b7c5c'
  on-primary-container: '#ffffff'
  inverse-primary: '#bacda8'
  secondary: '#805533'
  on-secondary: '#ffffff'
  secondary-container: '#fdc39a'
  on-secondary-container: '#794e2e'
  tertiary: '#635e4d'
  on-tertiary: '#ffffff'
  tertiary-container: '#7c7665'
  on-tertiary-container: '#ffffff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d6e9c2'
  primary-fixed-dim: '#bacda8'
  on-primary-fixed: '#111f07'
  on-primary-fixed-variant: '#3c4b2f'
  secondary-fixed: '#ffdcc5'
  secondary-fixed-dim: '#f4bb92'
  on-secondary-fixed: '#301400'
  on-secondary-fixed-variant: '#653d1e'
  tertiary-fixed: '#ebe2cd'
  tertiary-fixed-dim: '#cec6b2'
  on-tertiary-fixed: '#1f1b0f'
  on-tertiary-fixed-variant: '#4b4637'
  background: '#fcf9f8'
  on-background: '#1c1b1b'
  surface-variant: '#e5e2e1'
typography:
  headline-xl:
    fontFamily: Noto Serif
    fontSize: 48px
    fontWeight: '700'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Noto Serif
    fontSize: 32px
    fontWeight: '600'
    lineHeight: '1.3'
  headline-md:
    fontFamily: Noto Serif
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.4'
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 8px
  container-max: 1200px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 64px
  section-gap: 120px
---

## Brand & Style

This design system is anchored in the concept of "Slow Rituals." It captures the artisanal spirit of Benimaclet by blending Mediterranean warmth with modern minimalism. The visual language emphasizes quality over quantity, mirroring the craft of specialty coffee.

The style is a fusion of **Minimalism** and **Tactile** design. It utilizes heavy whitespace to evoke a sense of calm, paired with lifestyle photography that highlights physical textures—the grain of a ceramic cup, the swirl of steamed milk, and the natural morning light. The experience should feel approachable yet elevated, encouraging users to linger.

## Colors

The palette is derived from the organic materials found within a café environment, shifting the emphasis toward botanical and earthy tones. 

- **Primary (Sage Green):** The lead brand color, representing the natural origins of coffee and a commitment to sustainability. Used for primary actions and brand-heavy UI elements.
- **Secondary (Coffee Brown):** A rich, functional accent used for key interaction points and headings to ground the design in the artisanal craft of brewing.
- **Tertiary (Cream):** Now serving as the foundational surface color and background canvas. It provides a warmer feel than pure white, reducing eye strain and feeling more "paper-like."
- **Text (Dark Charcoal):** High-contrast legibility that avoids the harshness of pure black, maintaining the sophisticated aesthetic.

## Typography

The typography system relies on the contrast between an elegant, literary serif and a utilitarian sans-serif. 

**Noto Serif** is used for editorial moments, storytelling, and titles. It should be typeset with slightly tighter letter-spacing in larger sizes to maintain a premium feel.

**Inter** provides the functional backbone. It is used for all body text, navigation, and interface labels. For labels, a slightly increased letter-spacing and uppercase styling are recommended to create a clear distinction from narrative text.

## Layout & Spacing

This design system uses a **Fixed Grid** model to ensure content feels curated and intentional. On desktop, the content is centered within a 1200px container with generous 64px outer margins to create an "airy" boutique atmosphere.

Vertical rhythm is driven by large section gaps (120px+), allowing each piece of content or photography to "breathe." Gutters are kept wide to prevent the interface from feeling cluttered, reinforcing the minimalist philosophy.

## Elevation & Depth

Depth is conveyed through **Tonal Layers** rather than heavy shadows. Since the background is a rich Cream (#F5ECD7), elevation is achieved by:

1.  **Subtle Contrast:** Placing cards in a slightly lighter or white tint, or using a very thin (1px) border in a low-opacity Coffee Brown.
2.  **Soft Shadows:** When necessary, shadows should be extra-diffused with low opacity (5-10%) and tinted with the Secondary color (#8B5E3C) instead of grey, ensuring the warmth of the palette is preserved.
3.  **Layered Imagery:** Photography may slightly overlap containers to create a tactile, scrapbook-like depth.

## Shapes

The shape language is consistently **Rounded**, avoiding sharp geometric corners to maintain a friendly, organic feel. 

Buttons, input fields, and cards utilize a 0.5rem (8px) base radius. For larger containers or lifestyle image frames, a more pronounced 1.5rem (24px) radius may be used to emphasize the modern, approachable nature of the café.

## Components

### Buttons
Primary buttons use the **Sage Green** background with Cream text. They feature a subtle lift on hover. Secondary buttons utilize a Coffee Brown outline or a simple underline for a more minimalist appearance.

### Cards
Cards are used for menu items and blog posts. They should have a transparent or white background with a 1px border in a muted version of the Cream color. Images within cards should always use the `rounded-lg` setting.

### Inputs & Forms
Form fields are minimalist, featuring only a bottom border or a very light-colored fill. Focus states are highlighted using the **Coffee Brown** color for a warm, visible indicator.

### Chips & Tags
Used for coffee origins (e.g., "Ethiopia," "Wash Process"). These use the **Sage Green** at low opacity with dark text to feel like natural, botanical labels.

### Lifestyle Imagery
All images must feature soft, natural light. Use a "Fade In" scroll animation for images to reinforce the calm, slow-paced brand narrative. Avoid harsh flashes or high-saturation edits.