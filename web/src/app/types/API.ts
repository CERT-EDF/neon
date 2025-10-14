export interface APIResponse<T> {
  data: T;
  count: number;
}

export interface User {
  username: string;
  groups: string[];
}

export interface Identity {
  users: string[];
  groups: string[];
}

export interface PendingDownloadKey {
  guid: string;
  token: string;
}

export interface Info {
  api: string;
  version: string;
}

export interface Constant {
  tags: string[];
  globs: SecretPattern[];
  banner?: string;
  enums: {
    status: string[];
    opsystem: string[];
    indicator_nature: string[];
  };
  allow_empty_acs?: boolean;
}

export interface SecretPattern {
  glob: string;
  secret: string;
}

export interface AnalyzerInfo {
  name: string;
  tags: string[];
  version: string;
}
