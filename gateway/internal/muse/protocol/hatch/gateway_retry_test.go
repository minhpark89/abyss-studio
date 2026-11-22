package hatch

import (
	"context"
	"errors"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync/atomic"
	"testing"
	"time"

	"github.com/gorilla/websocket"
)

func TestGatewayUpgradeRetry(t *testing.T) {
	for _, tc := range []struct {
		name       string
		statuses   []int
		retryAfter string
		wantOK     bool
	}{
		{"temporary_502", []int{502, 502, 101}, "", true},
		{"persistent_502", []int{502, 502, 502}, "", false},
		{"session_expired", []int{401}, "", false},
		{"access_denied", []int{403}, "", false},
		{"rate_limited", []int{429}, "", false},
		{"service_requested_long_wait", []int{502}, "300", false},
	} {
		t.Run(tc.name, func(t *testing.T) {
			var calls atomic.Int32
			upgrader := websocket.Upgrader{}
			server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				index := int(calls.Add(1)) - 1
				if index >= len(tc.statuses) {
					http.Error(w, "excess request", 500)
					return
				}
				status := tc.statuses[index]
				if status == http.StatusSwitchingProtocols {
					socket, err := upgrader.Upgrade(w, r, nil)
					if err == nil {
						_ = socket.Close()
					}
					return
				}
				w.Header().Set("Retry-After", tc.retryAfter)
				w.WriteHeader(status)
			}))
			defer server.Close()
			wsURL := "ws" + strings.TrimPrefix(server.URL, "http")
			conn, err := openGatewaySocket(context.Background(), wsURL, &websocket.Dialer{}, []time.Duration{0, 0})
			if conn != nil {
				defer conn.Close()
			}
			if (err == nil) != tc.wantOK || int(calls.Load()) != len(tc.statuses) {
				t.Fatalf("attempts=%d err=%v", calls.Load(), err)
			}
		})
	}
}

func TestGatewayUpgradeRetryCanBeCancelled(t *testing.T) {
	var calls atomic.Int32
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		calls.Add(1)
		w.WriteHeader(http.StatusBadGateway)
		w.(http.Flusher).Flush()
	}))
	defer server.Close()
	timer := time.AfterFunc(100*time.Millisecond, cancel)
	defer timer.Stop()
	wsURL := "ws" + strings.TrimPrefix(server.URL, "http")
	_, err := openGatewaySocket(ctx, wsURL, &websocket.Dialer{}, []time.Duration{time.Minute})
	if !errors.Is(err, context.Canceled) || calls.Load() != 1 {
		t.Fatalf("attempts=%d err=%v", calls.Load(), err)
	}
}
