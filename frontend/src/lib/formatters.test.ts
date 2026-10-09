import { describe, it, expect } from "vitest";
import {
  formatCurrency,
  formatConsumption,
  formatDate,
  formatPercent,
  formatNumber,
} from "./formatters";

describe("formatters utils", () => {
  it("formats currency in Algerian Dinars (DA)", () => {
    const res = formatCurrency(6952.49);
    // Doit contenir 6 952,49 ou 6 952,49 et DA
    expect(res).toContain("DA");
    expect(res).toMatch(/6[\s\u202F]952,49/);
  });

  it("handles null or undefined currency", () => {
    expect(formatCurrency(null)).toBe("0,00 DA");
    expect(formatCurrency(undefined)).toBe("0,00 DA");
  });

  it("formats consumption with units", () => {
    expect(formatConsumption(692, "kWh")).toContain("kWh");
    expect(formatConsumption(17.5, "m³")).toContain("m³");
  });

  it("formats standard numbers with decimals", () => {
    expect(formatNumber(125.5, 2)).toMatch(/125,50/);
    expect(formatNumber(null)).toBe("0");
  });

  it("formats percentage with sign", () => {
    expect(formatPercent(5.2)).toContain("+5,2 %");
    expect(formatPercent(-3.1)).toContain("-3,1 %");
    expect(formatPercent(0)).toContain("0,0 %");
  });

  it("formats dates into French locale", () => {
    const res = formatDate("2026-06-16");
    expect(res).toContain("juin");
    expect(res).toContain("2026");
  });
});
