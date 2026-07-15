export interface Entitlement {
  featureKey: string;
  granted: boolean;
}

export interface BillingCustomerRef {
  userId: string;
  externalCustomerId?: string;
}

export interface BillingProvider {
  getEntitlements(customer: BillingCustomerRef): Promise<Entitlement[]>;
  hasFeature(customer: BillingCustomerRef, featureKey: string): Promise<boolean>;
  syncCustomer(customer: BillingCustomerRef): Promise<void>;
}
