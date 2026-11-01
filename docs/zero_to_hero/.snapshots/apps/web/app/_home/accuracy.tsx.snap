import { agesText, percent } from "@/lib/projection";
import type { PublishedModel } from "@/lib/published-model";

const cell = "py-2 pr-4 tabular-nums";

/**
 * The live accuracy table: the lines of the age model now deciding, as the API publishes them — measured, not
 * promised. For each age: how few of those just under it can pass, how few adults well over it are turned away, and
 * how often adults just over it are sent to a stronger check, the price of the first.
 */
export function Accuracy({ model }: { model: PublishedModel | null }) {
  if (model === null) {
    return <p className="mt-4 text-ink-600 dark:text-ink-400">The figures can't be loaded right now.</p>;
  }
  return (
    <>
      <table className="mt-6 w-full text-left text-sm">
        <thead className="text-xs uppercase text-ink-600 dark:text-ink-400">
          <tr>
            <th className="py-2 pr-4 font-medium">Age line</th>
            <th className="py-2 pr-4 font-medium">Under the age who pass, at most</th>
            <th className="py-2 pr-4 font-medium">Adults 3+ years over turned away, at most</th>
            <th className="py-2 font-medium">Adults just over sent to a stronger check</th>
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
                <td className={cell}>
                  {line.minorBound === null ? "not measured" : percent(line.minorBound)}
                </td>
                <td className={cell}>
                  {line.adultBound === null ? "not measured" : percent(line.adultBound)}
                </td>
                <td className="py-2 tabular-nums">
                  {youngest === undefined
                    ? "not measured"
                    : `${percent(youngest.stepUp)} of ${agesText(youngest.ages)}`}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <p className="mt-4 text-sm leading-relaxed text-ink-600 dark:text-ink-400">
        Model {model.version}
        {model.calibratedOn === null
          ? "."
          : `, measured on ${model.calibratedOn.faces === null ? "" : `${model.calibratedOn.faces.toLocaleString("en")} `}photos from the ${model.calibratedOn.name} dataset, whose ages were estimated rather than documented.`}{" "}
        "At most" is a 95 % upper bound for any single age in the five years under the line.{" "}
        {model.calibrated
          ? null
          : "These lines don't yet meet Dwarpal's own release standard (2 % for every age and group), so this model decides test checks only."}
      </p>
    </>
  );
}
