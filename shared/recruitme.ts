import { z } from "zod";

export const discoveryProviderIds = [
  "exa_free",
  "pdl_free",
  "apollo",
  "exa_keyed",
  "exa_people",
  "tavily",
  "brave",
  "serpapi",
] as const;
export const searchProviderSchema = z.object({
  id: z.enum(discoveryProviderIds),
  budget: z.number().min(0).max(5).multipleOf(0.01),
});

export const jobProfileSchema = z.object({
  id: z.string().uuid(),
  revision: z.number().int().nonnegative(),
  title: z.string().trim().min(3).max(120),
  roles: z.string().trim().min(3).max(600),
  locations: z.string().trim().min(3).max(600),
  fitTerms: z.string().trim().min(3).max(600),
  juniorRoles: z.string().max(400),
  maximumHourlyPay: z.number().positive().max(1000).nullable(),
  maximumAnnualPay: z.number().positive().max(1000000).nullable().default(null),
  minimumYears: z.number().int().min(0).max(50),
  startDate: z.string().max(100),
  travelPay: z.boolean(),
  relocation: z.string().max(500),
  notes: z.string().max(2000),
  runCap: z.number().min(0).max(5).multipleOf(0.01),
  durationMinutes: z.number().int().min(1).max(30),
  searchProviders: z
    .array(searchProviderSchema)
    .min(1)
    .max(8)
    .refine(
      rows => new Set(rows.map(row => row.id)).size === rows.length,
      "Duplicate provider"
    )
    .default([
      { id: "exa_free", budget: 0 },
      { id: "exa_keyed", budget: 1 },
      { id: "tavily", budget: 1 },
    ]),
});
export type JobProfile = z.infer<typeof jobProfileSchema>;
export const initialProfile: JobProfile = {
  id: "148cac39-faf4-435f-9339-b32c83cb8291",
  revision: 0,
  title: "Metro Atlanta Commercial Electricians",
  roles:
    "commercial electrician, journeyman electrician, journeyman wireman, electrical foreman",
  locations:
    "Covington, Conyers, Metro Atlanta, Doraville, Decatur, Lawrenceville, Marietta",
  fitTerms:
    "commercial construction, tenant buildout, conduit installation, switchgear installation, commercial wiring",
  juniorRoles: "",
  maximumHourlyPay: null,
  maximumAnnualPay: null,
  minimumYears: 3,
  startDate: "To be confirmed",
  travelPay: false,
  relocation:
    "Metro Atlanta targeting; relocation availability requires review.",
  notes:
    "Target 3–10 years of relevant commercial electrical experience. Verify person-attributed job-change signals and their original dates. Human review is required; discovery hints do not establish qualification or consent to contact.",
  runCap: 5,
  durationMinutes: 30,
  searchProviders: [
    { id: "exa_free", budget: 0 },
    { id: "exa_keyed", budget: 1 },
    { id: "tavily", budget: 1 },
  ],
};
