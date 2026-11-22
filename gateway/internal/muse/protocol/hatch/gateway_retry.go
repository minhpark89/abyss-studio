package hatch

import (
	"context"
	"errors"
	"fmt"
	"net/http"
	"strconv"
	"strings"
	"time"

	"github.com/gorilla/websocket"
)

// Only retry an explicitly rejected WebSocket upgrade, before a connection
// exists. A connected session, generation request, or uncertain send is never replayed here.
func openGatewaySocket(ctx context.Context, endpoint string, dialer *websocket.Dialer, delays []time.Duration) (*websocket.Conn, error) {
	for attempt := 0; ; attempt++ {
		conn, response, err := dialer.DialContext(ctx, endpoint, nil)
		if err == nil {
			return conn, nil
		}
		if response == nil {
			return nil, fmt.Errorf("gateway dial: %w", err)
		}
		if response.Body != nil {
			_ = response.Body.Close()
		}
		failure := fmt.Errorf("gateway dial: %w (%s)", err, response.Status)
		if !errors.Is(err, websocket.ErrBadHandshake) || response.StatusCode != http.StatusBadGateway || attempt >= len(delays) {
			return nil, failure
		}
		delay := delays[attempt]
		if value := strings.TrimSpace(response.Header.Get("Retry-After")); value != "" {
			var requested time.Duration
			if seconds, err := strconv.ParseUint(value, 10, 31); err == nil {
				requested = time.Duration(seconds) * time.Second
			} else if date, err := http.ParseTime(value); err == nil {
				requested = time.Until(date)
			} else {
				return nil, failure
			}
			if requested > time.Minute {
				return nil, failure
			}
			if requested > delay {
				delay = requested
			}
		}
		timer := time.NewTimer(delay)
		select {
		case <-ctx.Done():
			timer.Stop()
			return nil, ctx.Err()
		case <-timer.C:
		}
	}
}
