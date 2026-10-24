export function smsHref(e164Number: string): string {
  return `sms:${e164Number}`;
}

/** Formats US numbers as (XXX) XXX-XXXX; other numbers are shown as stored. */
export function formatPhoneNumber(e164Number: string): string {
  const us = /^\+1(\d{3})(\d{3})(\d{4})$/.exec(e164Number);
  return us ? `(${us[1]}) ${us[2]}-${us[3]}` : e164Number;
}
