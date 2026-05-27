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

  if (!isEmailDomainAllowed(normalizedEmail, allowedDomains)) {
    return buildAllowedDomainError(allowedDomains);
  }

  return null;
}

export function isEmailDomainAllowed(
  email: string,
  allowedDomains = getAllowedEmailDomains()
): boolean {
  if (allowedDomains.length === 0) {
    return true;
  }

  const domain = email.trim().toLowerCase().split("@").at(1);
  return Boolean(domain && allowedDomains.includes(domain));
}

export function buildAllowedDomainError(allowedDomains = getAllowedEmailDomains()): string {
  return `Use an approved email domain: ${allowedDomains.join(", ")}.`;
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
