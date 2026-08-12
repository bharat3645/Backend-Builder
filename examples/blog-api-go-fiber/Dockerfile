FROM golang:1.21-alpine AS build
WORKDIR /app
COPY go.mod ./
RUN go mod download || true
COPY . .
RUN go build -o server .

FROM alpine:3.19
RUN apk add --no-cache ca-certificates
WORKDIR /app
COPY --from=build /app/server .
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD wget -qO- http://localhost:8000/health || exit 1
CMD ["./server"]
