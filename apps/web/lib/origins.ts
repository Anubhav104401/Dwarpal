/** A project's allowed origins as a person types them — one per line, blank lines ignored — in the list the API
 * takes. The API checks each one and writes it the standard way (decision D29). */
export function originLines(text: string): string[] {
  return text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line !== "");
}
