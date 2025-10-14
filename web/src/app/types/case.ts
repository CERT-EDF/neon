export interface CaseMetadata {
  guid: string;
  created: string;
  updated: string;
  closed?: string;
  tsid?: string;
  name: string;
  description?: string;
  acs: string[];
  report?: string;

  unseenNew?: boolean; //Injected value in API getCases
}

export interface CaseSampleMetadata {
  guid: string;
  created: string;
  updated: string;
  name: string;
  size: number;
  tags: string[];
  report: string;
  digests: { [key: string]: string };
  symbols: { [key: number]: string };
  rulesets: { [key: string]: string };
  opsystem: string;
  indicators: SampleIndicator[];
  cname?: string;
  cguid?: string;
}

export interface SampleIndicator {
  value: string;
  nature: string;
  description?: string;
}

export interface SampleAnalysis {
  guid: string;
  created: string;
  updated: string;
  status: string;
  analyzer: string;
}
