// Auto-generated API Client for VintedBot
// Generated from OpenAPI specification

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';

class VintedBotAPI {

  /**
   * Ingest Photos
   */
  async ingest_photos_ingest_photos_post(data: any) {
    const response = await fetch(`${API_BASE}/ingest/photos`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    const contentType = response.headers.get('content-type');
    if (contentType?.includes('application/json')) {
      return response.json();
    } else if (contentType?.includes('text/')) {
      return response.text();
    } else {
      return response.blob();
    }
  }

  /**
   * Save Draft
   */
  async save_draft_ingest_save_draft_post(data: any) {
    const response = await fetch(`${API_BASE}/ingest/save-draft`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    const contentType = response.headers.get('content-type');
    if (contentType?.includes('application/json')) {
      return response.json();
    } else if (contentType?.includes('text/')) {
      return response.text();
    } else {
      return response.blob();
    }
  }

  /**
   * Get All Listings
   */
  async get_all_listings_listings_all_get() {
    const response = await fetch(`${API_BASE}/listings/all`, {
      method: 'GET',
    });
    const contentType = response.headers.get('content-type');
    if (contentType?.includes('application/json')) {
      return response.json();
    } else if (contentType?.includes('text/')) {
      return response.text();
    } else {
      return response.blob();
    }
  }

  /**
   * Get Listing
   */
  async get_listing_listings__item_id__get(item_id: string) {
    const response = await fetch(`${API_BASE}/listings/${item_id}`, {
      method: 'GET',
    });
    const contentType = response.headers.get('content-type');
    if (contentType?.includes('application/json')) {
      return response.json();
    } else if (contentType?.includes('text/')) {
      return response.text();
    } else {
      return response.blob();
    }
  }

  /**
   * Update Listing
   */
  async update_listing_listings__item_id__put(item_id: string, data: any) {
    const response = await fetch(`${API_BASE}/listings/${item_id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    const contentType = response.headers.get('content-type');
    if (contentType?.includes('application/json')) {
      return response.json();
    } else if (contentType?.includes('text/')) {
      return response.text();
    } else {
      return response.blob();
    }
  }

  /**
   * Delete Listing
   */
  async delete_listing_listings__item_id__delete(item_id: string) {
    const response = await fetch(`${API_BASE}/listings/${item_id}`, {
      method: 'DELETE',
    });
    const contentType = response.headers.get('content-type');
    if (contentType?.includes('application/json')) {
      return response.json();
    } else if (contentType?.includes('text/')) {
      return response.text();
    } else {
      return response.blob();
    }
  }

  /**
   * Get Listings By Status
   */
  async get_listings_by_status_listings_status__status__get(status: string) {
    const response = await fetch(`${API_BASE}/listings/status/${status}`, {
      method: 'GET',
    });
    const contentType = response.headers.get('content-type');
    if (contentType?.includes('application/json')) {
      return response.json();
    } else if (contentType?.includes('text/')) {
      return response.text();
    } else {
      return response.blob();
    }
  }

  /**
   * Simulate Pricing
   */
  async simulate_pricing_pricing_simulate_post(data: any) {
    const response = await fetch(`${API_BASE}/pricing/simulate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    const contentType = response.headers.get('content-type');
    if (contentType?.includes('application/json')) {
      return response.json();
    } else if (contentType?.includes('text/')) {
      return response.text();
    } else {
      return response.blob();
    }
  }

  /**
   * Export Csv
   */
  async export_csv_export_csv_get() {
    const response = await fetch(`${API_BASE}/export/csv`, {
      method: 'GET',
    });
    const contentType = response.headers.get('content-type');
    if (contentType?.includes('application/json')) {
      return response.json();
    } else if (contentType?.includes('text/')) {
      return response.text();
    } else {
      return response.blob();
    }
  }

  /**
   * Export Vinted
   */
  async export_vinted_export_vinted_get() {
    const response = await fetch(`${API_BASE}/export/vinted`, {
      method: 'GET',
    });
    const contentType = response.headers.get('content-type');
    if (contentType?.includes('application/json')) {
      return response.json();
    } else if (contentType?.includes('text/')) {
      return response.text();
    } else {
      return response.blob();
    }
  }

  /**
   * Export Json
   */
  async export_json_export_json_get() {
    const response = await fetch(`${API_BASE}/export/json`, {
      method: 'GET',
    });
    const contentType = response.headers.get('content-type');
    if (contentType?.includes('application/json')) {
      return response.json();
    } else if (contentType?.includes('text/')) {
      return response.text();
    } else {
      return response.blob();
    }
  }

  /**
   * Export Pdf
   */
  async export_pdf_export_pdf_get() {
    const response = await fetch(`${API_BASE}/export/pdf`, {
      method: 'GET',
    });
    const contentType = response.headers.get('content-type');
    if (contentType?.includes('application/json')) {
      return response.json();
    } else if (contentType?.includes('text/')) {
      return response.text();
    } else {
      return response.blob();
    }
  }

  /**
   * Get Stats
   */
  async get_stats_stats_get() {
    const response = await fetch(`${API_BASE}/stats`, {
      method: 'GET',
    });
    const contentType = response.headers.get('content-type');
    if (contentType?.includes('application/json')) {
      return response.json();
    } else if (contentType?.includes('text/')) {
      return response.text();
    } else {
      return response.blob();
    }
  }

  /**
   * Get Health
   */
  async get_health_health_get() {
    const response = await fetch(`${API_BASE}/health`, {
      method: 'GET',
    });
    const contentType = response.headers.get('content-type');
    if (contentType?.includes('application/json')) {
      return response.json();
    } else if (contentType?.includes('text/')) {
      return response.text();
    } else {
      return response.blob();
    }
  }

  /**
   * Generate Test Photoset
   */
  async generate_test_photoset_bonus_test_photoset_get() {
    const response = await fetch(`${API_BASE}/bonus/test/photoset`, {
      method: 'GET',
    });
    const contentType = response.headers.get('content-type');
    if (contentType?.includes('application/json')) {
      return response.json();
    } else if (contentType?.includes('text/')) {
      return response.text();
    } else {
      return response.blob();
    }
  }

  /**
   * Get Recommendations
   */
  async get_recommendations_bonus_recommendations_get() {
    const response = await fetch(`${API_BASE}/bonus/recommendations`, {
      method: 'GET',
    });
    const contentType = response.headers.get('content-type');
    if (contentType?.includes('application/json')) {
      return response.json();
    } else if (contentType?.includes('text/')) {
      return response.text();
    } else {
      return response.blob();
    }
  }

  /**
   * Simulate Multiple Prices
   */
  async simulate_multiple_prices_bonus_simulate_multi_price_post(data: any) {
    const response = await fetch(`${API_BASE}/bonus/simulate/multi-price`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    const contentType = response.headers.get('content-type');
    if (contentType?.includes('application/json')) {
      return response.json();
    } else if (contentType?.includes('text/')) {
      return response.text();
    } else {
      return response.blob();
    }
  }

  /**
   * Import Csv
   */
  async import_csv_import_csv_post(data: any) {
    const response = await fetch(`${API_BASE}/import/csv`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    const contentType = response.headers.get('content-type');
    if (contentType?.includes('application/json')) {
      return response.json();
    } else if (contentType?.includes('text/')) {
      return response.text();
    } else {
      return response.blob();
    }
  }

  /**
   * Root
   */
  async root__get() {
    const response = await fetch(`${API_BASE}/`, {
      method: 'GET',
    });
    const contentType = response.headers.get('content-type');
    if (contentType?.includes('application/json')) {
      return response.json();
    } else if (contentType?.includes('text/')) {
      return response.text();
    } else {
      return response.blob();
    }
  }
}

export const api = new VintedBotAPI();
