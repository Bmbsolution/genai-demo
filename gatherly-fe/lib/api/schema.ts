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
      location: string | null;
      capacity: number | null;
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
      location?: string | null;
      capacity?: number | null;
    };
    GuestResponse: {
      id: string;
      event_id: string;
      name: string;
      email: string;
      rsvp_status: string;
      invite_token: string;
      created_at: string;
    };
    GuestCreateRequest: {
      name: string;
      email: string;
    };
    RsvpView: {
      guest_name: string;
      rsvp_status: string;
      event: {
        title: string;
        starts_at: string;
        location: string | null;
      };
    };
    RsvpUpdateRequest: {
      rsvp_status: string;
    };
  };
}
