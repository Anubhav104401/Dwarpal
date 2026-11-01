import { getLocale, getTranslations } from "next-intl/server";

import { agesText, percent } from "@/lib/projection";
import type { PublishedModel } from "@/lib/published-model";

const cell = "py-2 pr-4 tabular-nums";

/**
 * The live accuracy table: the lines of the age model now deciding, as the API publishes them — measured, not
 * promised. For each age: how few of those just under it can pass, how few adults well over it are turned away, and
 * how often adults just over it are sent to a stronger check, the price of the first.
 */
export async function Accuracy({ model }: { model: PublishedModel | null }) {
  const t = await getTranslations("Accuracy");
  const locale = await getLocale();
  if (model === null) {
    return <p className="mt-4 text-ink-600 dark:text-ink-400">{t("unavailable")}</p>;
  }
  const notMeasured = t("notMeasured");
  return (
    <>
      <table className="mt-6 w-full text-left text-sm">
        <thead className="text-xs uppercase text-ink-600 dark:text-ink-400">
          <tr>
            <th className="py-2 pr-4 font-medium">{t("line")}</th>
            <th className="py-2 pr-4 font-medium">{t("minors")}</th>
            <th className="py-2 pr-4 font-medium">{t("adults")}</th>
            <th className="py-2 font-medium">{t("stepUp")}</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-ink-200 dark:divide-white/10">
          {model.lines.map((line) => {
            const youngest = line.adults[0];
            return (
              <tr key={line.minAge}>
                <th scope="row" className="py-2 pr-4 font-semibold">
                  {line.minAge}+
                </th>
                <td className={cell}>{line.minorBound === null ? notMeasured : percent(line.minorBound)}</td>
                <td className={cell}>{line.adultBound === null ? notMeasured : percent(line.adultBound)}</td>
                <td className="py-2 tabular-nums">
                  {youngest === undefined
                    ? notMeasured
                    : t("share", { share: percent(youngest.stepUp), ages: agesText(youngest.ages) })}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <p className="mt-4 text-sm leading-relaxed text-ink-600 dark:text-ink-400">
        {model.calibratedOn === null
          ? t("model", { version: model.version })
          : t("measuredOn", {
              version: model.version,
              faces: model.calibratedOn.faces === null ? "" : model.calibratedOn.faces.toLocaleString(locale),
              dataset: model.calibratedOn.name,
            })}{" "}
        {t("bound")} {model.calibrated ? null : t("uncalibrated")}
      </p>
    </>
  );
}
