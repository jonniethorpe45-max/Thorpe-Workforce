import type { BillingCustomerRef, BillingProvider, Entitlement } from './types';

export class MockBillingProvider implements BillingProvider {
  async getEntitlements(_customer: BillingCustomerRef): Promise<Entitlement[]> {
    return [];
  }

  async hasFeature(_customer: BillingCustomerRef, _featureKey: string): Promise<boolean> {
    return false;
  }

  async syncCustomer(_customer: BillingCustomerRef): Promise<void> {
    return;
  }
}
