export interface AuthParams {
  type: string;
  parameters: OIDCParams | undefined;
}

export interface OIDCParams {
  host: string;
  client: string;
  realm: string;
  redirect_uri: string;
  include_auth?: boolean;
}

export interface Token {
  access: string;
  refresh: string;
  expires_in: number;
  refresh_expires_in: number;
}
