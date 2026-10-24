import { TextAggreyLink } from "@/components/TextAggreyLink";
import { sampleQuestions } from "@/content/sampleQuestions";
import { getAggreyPhoneNumber } from "@/lib/config";

import styles from "./page.module.css";

export default function Home() {
  const phoneNumber = getAggreyPhoneNumber();

  return (
    <main className={styles.main}>
      <section className={styles.hero}>
        <h1 className={styles.title}>Aggrey</h1>
        <p className={styles.lead}>Should I go to the caf? Text Aggrey and find out in seconds.</p>
        <p>
          Ask what&apos;s being served, when a meal starts or ends, or whether a food is on the
          menu. No app to download and no account to create.
        </p>
        <TextAggreyLink phoneNumber={phoneNumber} />
      </section>

      <section className={styles.examples} aria-labelledby="examples-heading">
        <h2 id="examples-heading">Try asking</h2>
        <ul className={styles.questions}>
          {sampleQuestions.map((question) => (
            <li key={question}>{question}</li>
          ))}
        </ul>
      </section>
    </main>
  );
}
