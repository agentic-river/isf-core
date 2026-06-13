# React Component Guidelines

## Objective
This document outlines the strict guidelines and conventions for writing React components in this project, ensuring high code quality and maintainability.

## 1. Core Principles
- **Functional Components:** You MUST always use functional components with React Hooks. Class components are forbidden.
- **Predictability:** You MUST ensure components are pure and predictable, keeping presentation logic separated from business logic.
- **Type Checking:** You MUST provide meaningful `PropTypes` or use TypeScript interfaces for robust type checking.

## 2. Naming Conventions
- You MUST name your component files and functions using `PascalCase`.

## 3. Examples

### 🟢 Good Example
*   **Good:** 
    ```jsx
    import React, { useState } from 'react';
    import PropTypes from 'prop-types';

    export const UserProfile = ({ user }) => {
      const [isExpanded, setIsExpanded] = useState(false);
      return <div>{user.name}</div>;
    };

    UserProfile.propTypes = {
      user: PropTypes.shape({ name: PropTypes.string }).isRequired,
    };
    ```

### 🔴 Bad Example
*   **Bad:** Using class components or skipping prop validations.
    ```jsx
    export class userProfile extends React.Component {
      render() {
        return <div>{this.props.user.name}</div>;
      }
    }
    ```