// Helpers shared by the cmdlet-editing components.
export function deepClone(value) {
  return JSON.parse(JSON.stringify(value));
}
