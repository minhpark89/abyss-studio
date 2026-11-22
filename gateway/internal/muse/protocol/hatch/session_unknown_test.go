package hatch

import (
	"context"
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"net/url"
	"testing"
	"time"
)

func TestUnknownInventoryStillRequiresProviderAdmission(t *testing.T) {
	for _, status := range []int{http.StatusOK, http.StatusForbidden} {
		t.Run(http.StatusText(status), func(t *testing.T) {
			wakes, admissions := 0, 0
			server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				switch r.URL.Path {
				case "/api/session":
					_, _ = w.Write([]byte(`{"status":"assigned","vm_id":"vm1","endpoint_url":"https://vm1","vm_state":"UNKNOWN"}`))
				case "/api/hatch/vm/wake":
					wakes++
					w.WriteHeader(http.StatusForbidden)
				case "/api/hatch/token":
					admissions++
					if r.Header.Get("Sec-Fetch-Site") != "same-origin" || r.Header.Get("Cookie") != "hatch_sess=authorized-test-session" {
						t.Error("normal authenticated application headers were lost")
					}
					w.WriteHeader(status)
					if status == http.StatusOK {
						_, _ = w.Write([]byte(`{"token":"provider-issued-test-token"}`))
					} else {
						_, _ = w.Write([]byte(`{"error":"Forbidden"}`))
					}
				case "/api/hatch/noise-notary-token":
					_, _ = w.Write([]byte(`{"notaryToken":"test-notary"}`))
				default:
					t.Errorf("unexpected route %s", r.URL.Path)
					w.WriteHeader(http.StatusNotFound)
				}
			}))
			defer server.Close()
			base, _ := url.Parse(server.URL)
			ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
			defer cancel()
			session, err := Bootstrap(ctx, SessionOptions{BaseURL: base, Client: server.Client(), Cookies: map[string]string{"hatch_sess": "authorized-test-session"}})
			if wakes != 0 || admissions == 0 {
				t.Fatalf("inventory blocked admission: wakes=%d admissions=%d", wakes, admissions)
			}
			if status == http.StatusOK {
				if err != nil || session == nil || session.AuthToken != "provider-issued-test-token" {
					t.Fatalf("authorized admission failed: %v", err)
				}
			} else {
				var authErr *AuthError
				if session != nil || !errors.As(err, &authErr) || authErr.Status != http.StatusForbidden || admissions > 2 {
					t.Fatalf("provider denial must remain terminal: session=%v err=%v calls=%d", session != nil, err, admissions)
				}
			}
		})
	}
}

func TestRecoveryWakesOnlyTheSameAssignedUnknownMachine(t *testing.T) {
	for _, tc := range []struct {
		name, assignedID, state, status string
		wakes                           int
	}{
		{"same", "vm1", "UNKNOWN", "assigned", 1},
		{"already_running", "vm1", "RUNNING", "assigned", 0},
		{"assignment_changed", "vm2", "UNKNOWN", "assigned", 0},
		{"not_assigned", "vm1", "UNKNOWN", "none", 0},
	} {
		t.Run(tc.name, func(t *testing.T) {
			var wakes, inventory, admissions int
			server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				switch r.URL.Path {
				case "/api/session":
					inventory++
					json.NewEncoder(w).Encode(map[string]string{"status": tc.status, "vm_id": tc.assignedID, "vm_state": tc.state, "endpoint_url": "https://test-machine"})
				case "/api/hatch/vm/wake":
					wakes++
					var body map[string]any
					if err := json.NewDecoder(r.Body).Decode(&body); err != nil || body["vm_id"] != "vm1" {
						t.Error("wrong wake target")
					}
					w.Write([]byte("{}"))
				case "/api/hatch/token":
					admissions++
					w.Write([]byte(`{"token":"test-admission"}`))
				case "/api/hatch/noise-notary-token":
					w.Write([]byte("{}"))
				default:
					t.Errorf("unexpected route %s", r.URL.Path)
				}
			}))
			defer server.Close()
			base, _ := url.Parse(server.URL)
			_, err := bootstrap(context.Background(), SessionOptions{BaseURL: base, Client: server.Client()}, "vm1")
			if err != nil || wakes != tc.wakes || inventory != 1+tc.wakes || admissions != 1 {
				t.Fatalf("err=%v inventory=%d wakes=%d admissions=%d", err, inventory, wakes, admissions)
			}
		})
	}
}
