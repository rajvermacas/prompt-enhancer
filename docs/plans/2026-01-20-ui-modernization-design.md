# UI Modernization Design

## Overview

Modernize the existing FastAPI + Jinja2 + Tailwind CSS application with a fluid, professional UI while maintaining the red/black color theme.

**Design Philosophy:**
- Subtle, professional aesthetic (Linear/Notion inspired)
- Gentle micro-interactions (200-300ms transitions)
- Desktop-first with responsive fallbacks
- Sticky header with backdrop blur

---

## 1. Color Palette Refinement

| Element | Current | New |
|---------|---------|-----|
| Header bg | `bg-black` | `bg-black/90 backdrop-blur-md` |
| Primary accent | `red-600` | Keep `red-600` |
| Hover accent | - | `red-500` |
| Card backgrounds | `bg-white` | `bg-white` with `shadow-sm` → `shadow-md` hover |
| Borders | `border-gray-300` | `border-gray-200` (softer) |
| Secondary text | `text-gray-600` | `text-gray-500` |

**Spacing & Typography:**
- Card padding: `p-4` → `p-6`
- Section gaps: `gap-6`
- Line-height: `leading-relaxed`
- Font weights: titles `font-semibold`, body `font-normal`

---

## 2. Header & Navigation

**Sticky Header:**
- Position: `sticky top-0 z-50`
- Background: `bg-black/90 backdrop-blur-md`
- Border: `border-b border-white/10`
- Shadow on scroll: add `shadow-md` when `scrollY > 0`

**Navigation Links:**
- Default: `text-gray-400`
- Hover: `text-white` + `translateY(-1px)`, 200ms transition
- Active: `text-white` + `border-b-2 border-red-600`

**Workspace Dropdown:**
- Trigger: `bg-white/10 rounded-lg`, hover `bg-white/20`
- Panel: `bg-gray-900 shadow-xl rounded-lg`
- Animation: `scale-95 opacity-0` → `scale-100 opacity-1`, 200ms
- Items: hover `bg-white/10`

**New Workspace Button:**
- Ghost style: `border border-red-600 text-red-600`
- Hover: `bg-red-600 text-white` fill transition

---

## 3. Cards & Content Containers

**Base Card:**
- Background: `bg-white`
- Border: `border border-gray-100`
- Shadow: `shadow-sm` → `shadow-md` on hover
- Radius: `rounded-xl`
- Padding: `p-6`

**Card Hover:**
- Transform: `translateY(-2px)`
- Transition: 200ms ease

**News Article Card Structure:**
```
┌──────────────────────────────────────────────────────────────┐
│  Headline Title                                    [Category]│
│                                                              │
│  Content preview text that truncates elegantly...            │
│                                                              │
│  ─────────────────────────────────────────────────────────── │
│  [Start AI Workflow]                          Confidence: 85%│
└──────────────────────────────────────────────────────────────┘
```

**Category Badge:**
- Style: `bg-red-50 text-red-700 px-3 py-1 rounded-full text-sm font-medium`

**Expandable AI Insight Section:**
- Animation: `max-height` + `overflow-hidden`, 300ms ease
- Left accent: `border-l-2 border-red-600`
- Background: `bg-gray-50`

---

## 4. Buttons & Interactive Elements

**Primary Button (Red):**
- Base: `bg-red-600 text-white px-5 py-2.5 rounded-lg font-medium`
- Hover: `bg-red-500 translateY(-1px)`
- Active: `bg-red-700 translateY(0)`
- Focus: `ring-2 ring-red-600/50 ring-offset-2`
- Transition: 200ms

**Secondary Button (Gray):**
- Base: `bg-gray-100 text-gray-700 px-5 py-2.5 rounded-lg font-medium`
- Hover: `bg-gray-200` + subtle lift
- Active: `bg-gray-300`

**Ghost/Outline Button:**
- Base: `border border-gray-300 text-gray-700 bg-transparent`
- Hover: `bg-gray-50 border-gray-400`

**Icon Buttons:**
- Size: `w-9 h-9` centered
- Hover: `bg-gray-100 rounded-lg`
- Transition: 150ms

**Feedback Buttons:**
- Correct: `bg-green-50 text-green-700 border border-green-200`
- Incorrect: `bg-red-50 text-red-700 border border-red-200`
- Hover: border opacity increase + slight lift

**Form Inputs:**
- Base: `border border-gray-200 rounded-lg px-4 py-2.5 bg-white`
- Focus: `border-red-600 ring-2 ring-red-600/20`
- Placeholder: `text-gray-400`
- Transition: 150ms

**Disabled State:**
- `opacity-50 cursor-not-allowed`

---

## 5. Modals & Overlays

**Backdrop:**
- Style: `bg-black/60 backdrop-blur-sm`
- Animation: fade in 200ms

**Modal Container:**
- Background: `bg-white`
- Radius: `rounded-2xl`
- Shadow: `shadow-2xl`
- Max-width: `max-w-2xl w-full mx-4`
- Animation: `scale-95 opacity-0` → `scale-100 opacity-100`, 200ms

**Modal Header:**
- Border: `border-b border-gray-100` (remove heavy red top border)
- Title: `text-xl font-semibold text-gray-900`
- Close button: `w-9 h-9` ghost button top-right

**Modal Body:**
- Padding: `p-6`
- Max-height: `max-h-[70vh] overflow-y-auto`

**Modal Footer:**
- Border: `border-t border-gray-100`
- Padding: `p-4`
- Buttons: aligned right with `gap-3`

---

## 6. Loading States & Micro-interactions

**Loading Spinner:**
- Style: `w-5 h-5 border-2 border-red-600 border-t-transparent animate-spin`
- Or: skeleton loaders with gray shimmer for cards

**Button Loading:**
- Inline spinner replacing text
- Maintain button width
- `opacity-80 cursor-wait`

**Animation Timing:**

| Element | Interaction | Animation | Duration |
|---------|-------------|-----------|----------|
| Cards | Hover | `translateY(-2px)` + shadow | 200ms |
| Buttons | Hover | `translateY(-1px)` | 150ms |
| Buttons | Active | `translateY(0)` | 100ms |
| Nav links | Hover | color + `translateY(-1px)` | 200ms |
| Dropdowns | Open/Close | scale + fade | 200ms |
| Modals | Open | backdrop fade + scale | 200ms |
| Expandable | Toggle | max-height + opacity | 300ms |
| Form focus | Focus | ring fade-in | 150ms |

**Feedback:**
- Success: green checkmark fade in/out
- Error: subtle shake animation (300ms)
- Header: shadow appears on scroll

---

## 7. Responsive Breakpoints

**Desktop (default, 1280px+):**
- Container: `max-w-6xl`
- Padding: `px-8`
- Full card features

**Tablet (md, 768px):**
- Padding: `px-6`
- Card padding: `p-5`

**Mobile (sm, 640px):**
- Padding: `px-4`
- Card padding: `p-4`
- Modals: `mx-2 rounded-xl`
- Buttons: `w-full` on forms
- Tap targets: minimum 44px height
- Use `active:` instead of `hover:` states

---

## Implementation Files

1. **`base.html`** - Header, navigation, global styles, scroll detection JS
2. **`news_list.html`** - Card styles, expandable sections, feedback buttons
3. **`prompts.html`** - Tab navigation, form styling, card updates

## CSS Strategy

All styling via Tailwind utility classes (no custom CSS files needed). Add custom transition utilities if needed via Tailwind config inline.
