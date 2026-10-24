import { formatPhoneNumber, smsHref } from "@/lib/sms";

import styles from "./TextAggreyLink.module.css";

type Props = {
  phoneNumber: string | null;
};

export function TextAggreyLink({ phoneNumber }: Props) {
  if (!phoneNumber) {
    return <p className={styles.missing}>The Aggrey number is not configured yet.</p>;
  }

  return (
    <div className={styles.wrapper}>
      <a className={styles.button} href={smsHref(phoneNumber)}>
        Text Aggrey
      </a>
      <p className={styles.number}>
        Or text <span className={styles.digits}>{formatPhoneNumber(phoneNumber)}</span>
      </p>
    </div>
  );
}
