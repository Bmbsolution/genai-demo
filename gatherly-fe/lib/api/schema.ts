/** Hand-written API types for the Gatherly backend (mirrors the Pydantic schemas). */

export interface PageMeta {
  limit: number;
  offset: number;
  total: number;
}

export interface components {
  schemas: {
    TokenPairResponse: {
      access_token: string;
      refresh_token: string;
      token_type: string;
    };
    UserResponse: {
      id: string;
      email: string;
      display_name: string;
      role: string;
      avatar_url: string | null;
      timezone: string;
      auth_provider: string;
    };
    EventResponse: {
      id: string;
      owner_id: string;
      title: string;
      description: string | null;
      starts_at: string;
      ends_at: string | null;
      location: string | null;
      cover_image_url: string | null;
      capacity: number | null;
      visibility: string;
      status: string;
      created_at: string;
    };
    EventListResponse: {
      data: components["schemas"]["EventResponse"][];
      meta: PageMeta;
    };
    EventCreateRequest: {
      title: string;
      description?: string | null;
      starts_at: string;
      ends_at?: string | null;
      location?: string | null;
      cover_image_url?: string | null;
      capacity?: number | null;
      visibility?: string;
    };
    GuestResponse: {
      id: string;
      event_id: string;
      name: string;
      email: string;
      rsvp_status: string;
      plus_one: boolean;
      dietary_notes: string | null;
      checked_in_at: string | null;
      invite_token: string;
      created_at: string;
    };
    GuestCreateRequest: {
      name: string;
      email: string;
    };
    GuestImportRequest: {
      csv: string;
    };
    GuestImportResponse: {
      created: number;
      skipped_duplicate: number;
      skipped_invalid: number;
      errors: string[];
    };
    CheckInRequest: {
      checked_in: boolean;
    };
    ReminderResponse: {
      sent: number;
    };
    EventInsightsResponse: {
      total_guests: number;
      responded: number;
      response_rate: number;
      attending: number;
      waitlisted: number;
      plus_ones: number;
      checked_in: number;
      dietary_notes: number;
      capacity: number | null;
      remaining_capacity: number | null;
      status_counts: Record<string, number>;
    };
    ReadinessCheckResponse: {
      key: string;
      passed: boolean;
      severity: string;
    };
    EventReadinessResponse: {
      ready: boolean;
      passed: number;
      total: number;
      checks: components["schemas"]["ReadinessCheckResponse"][];
    };
    RsvpView: {
      guest_name: string;
      rsvp_status: string;
      plus_one: boolean;
      dietary_notes: string | null;
      event: {
        title: string;
        description: string | null;
        starts_at: string;
        ends_at: string | null;
        location: string | null;
        cover_image_url: string | null;
      };
    };
    RsvpUpdateRequest: {
      rsvp_status: string;
      plus_one?: boolean;
      dietary_notes?: string | null;
    };
  };
}
