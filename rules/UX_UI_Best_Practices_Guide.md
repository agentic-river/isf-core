# 🎨 UX/UI Best Practices Guide

## Objective
This document outlines the core User Experience (UX) and User Interface (UI) principles that all frontend applications in this repository MUST follow. Following these guidelines ensures an intuitive, accessible, and consistent experience for all users.

## 1. Core User Experience (UX) Principles

*   **Clarity over Cleverness:** You MUST ensure navigation is intuitive and actions are obvious.
*   **Consistency and Standards:** You MUST use consistent button styles, navigation placements, and standard icons across the application.
*   **System Status & Feedback:** ALWAYS keep the user informed. You MUST show loading spinners for data fetches and toast notifications for success/error states.
*   **Error Prevention and Recovery:** You MUST validate inputs early and provide clear, actionable error messages instead of generic codes.

## 2. Core User Interface (UI) Principles

*   **Visual Hierarchy:** You MUST guide the user's eye using size, color, and contrast. Only use ONE Primary Call to Action (CTA) per view.
*   **Spacing & Whitespace:** You MUST follow an 8-Point Grid System (margins/padding in multiples of 8px).
*   **Typography:** Body text MUST be at least 16px. Limit font families to a maximum of two.

## 3. Accessibility (A11y) & Inclusivity

*   **Color and Contrast:** You MUST aim for a WCAG contrast ratio of at least 4.5:1 for normal text. NEVER rely on color alone to convey meaning (e.g., add an icon for errors).
*   **Keyboard Navigation:** Interactive elements MUST have visible `:focus` states.
*   **Semantic HTML:** ALWAYS use `<button>` for actions and `<a>` for navigation links. Provide `aria-labels` for icon-only buttons.

## 4. Forms & Data Input

*   **Layout & Labels:** You MUST use top-aligned labels. NEVER use placeholder text as a replacement for labels.
*   **Inline Validation:** You SHOULD validate user input immediately where possible (e.g., on `blur`).

## 5. Mobile & Responsive Design

*   **Touch Targets:** Buttons and interactive elements MUST be at least 44x44 pixels.
*   **Mobile-First Mindset:** You MUST design for the smallest screen first. Ensure tables scroll horizontally on mobile devices.

## 6. Examples

### 🟢 Good Examples
*   **Good Feedback:** Displaying a skeleton screen while fetching a list of items, followed by a toast notification saying "Items loaded successfully".
*   **Good Hierarchy:** Having a solid blue "Save" button (Primary) and an outlined "Cancel" button (Secondary).
*   **Good A11y:** `<button aria-label="Close dialog"><IconClose /></button>`
*   **Good Spacing:** `<div className="p-4 mb-8">` (16px padding, 32px bottom margin).

### 🔴 Bad Examples
*   **Bad Feedback:** Clicking a button and nothing happens until a response is returned 3 seconds later.
*   **Bad Hierarchy:** Having three solid primary buttons side-by-side on a single form.
*   **Bad A11y:** `<div onClick={closeDialog}><IconClose /></div>` (Using a div for a button action, no aria-label, no keyboard focus).
*   **Bad Spacing:** `<div className="p-[5px] mt-[13px]">` (Arbitrary spacing that does not follow the 8-point grid).
