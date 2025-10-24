# Contributing to WhisperNet

Thank you for your interest in contributing to **WhisperNet**!  
We welcome all forms of contributions — from fixing bugs to improving documentation and proposing new features.  
Please read through the following guidelines before making any changes.

---

## 🧭 Contribution Workflow

Follow these steps to ensure a smooth contribution process:

1. **Fork**
   - Fork the [saidhury/whispernet](https://github.com/saidhury/whispernet) repository to your GitHub account.

2. **Clone**
   - Clone your forked repository to your local machine:
     ```bash
     git clone https://github.com/YOUR_USERNAME/whispernet.git
     ```

3. **Branch**
   - Create a new branch with a descriptive name using the convention:
     ```
     type/scope
     ```
     **Examples:**
     - `feat/user-nicknames`
     - `fix/chat-overflow`
     - `docs/readme-updates`

4. **Develop**
   - Set up your development environment as described in the [README.md](./README.md).
   - Make your changes and ensure your code follows the existing style and structure.

5. **Commit**
   - Commit your changes using the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification.
   - Format:
     ```bash
     git commit -m "type(scope): short description"
     ```
     **Examples:**
     - `feat(api): add health check endpoint`
     - `fix(ui): resolve chat message overflow issue`
     - `docs(contributing): update contribution steps`

6. **Push**
   - Push your branch to your forked repository:
     ```bash
     git push origin type/scope
     ```

7. **Pull Request**
   - Open a pull request (PR) from your branch to the `main` branch of the upstream repository.
   - Ensure your PR follows the guidelines below.

---

## 📝 Pull Request Guidelines

- **Title:**  
  Must follow the Conventional Commits format (`type(scope): description`).

- **Description:**  
  Clearly describe what changes were made and why.  
  If the PR fixes an issue, link it using the format:
