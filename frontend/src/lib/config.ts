const E164 = /^\+[1-9]\d{7,14}$/;

/**
 * Aggrey's texting number, or null when it is not configured.
 *
 * NEXT_PUBLIC_ values are inlined at build time, so a production build without
 * a valid number fails instead of shipping a page with a broken text link.
 */
export function getAggreyPhoneNumber(): string | null {
  const value = process.env.NEXT_PUBLIC_AGGREY_PHONE_NUMBER?.trim() ?? "";

  if (E164.test(value)) {
    return value;
  }

  if (process.env.NODE_ENV === "production") {
    throw new Error(
      "NEXT_PUBLIC_AGGREY_PHONE_NUMBER must be set to an E.164 number (for example +1 and 10 digits). See frontend/.env.example.",
    );
  }

  return null;
}
