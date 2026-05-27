const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const MIN_PASSWORD_LENGTH = 8;

export function getAllowedEmailDomains(): string[] {
  return (process.env.NEXT_PUBLIC_ALLOWED_EMAIL_DOMAINS ?? "")
    .split(",")
    .map((domain) => domain.trim().toLowerCase())
    .filter(Boolean);
}

export function validateEmail(email: string): string | null {
  const normalizedEmail = email.trim().toLowerCase();

  if (!normalizedEmail) {
    return "Email is required.";
  }

  if (!EMAIL_PATTERN.test(normalizedEmail)) {
    return "Enter a valid email address.";
  }

  const allowedDomains = getAllowedEmailDomains();

  if (allowedDomains.length > 0) {
    const domain = normalizedEmail.split("@").at(1);

    if (!domain || !allowedDomains.includes(domain)) {
      return `Use an approved email domain: ${allowedDomains.join(", ")}.`;
    }
  }

  return null;
}

export function validatePassword(password: string): string | null {
  if (!password) {
    return "Password is required.";
  }

  if (password.length < MIN_PASSWORD_LENGTH) {
    return `Password must be at least ${MIN_PASSWORD_LENGTH} characters.`;
  }

  return null;
}
