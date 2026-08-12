package main

import (
	"log"
	"os"

	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/cors"
	"github.com/gofiber/fiber/v2/middleware/logger"
	"github.com/gofiber/fiber/v2/middleware/recover"

	"github.com/backend-builder/blog-api/database"
	"github.com/backend-builder/blog-api/models"
	"github.com/backend-builder/blog-api/routes"
)

func main() {
	db := database.Connect()

	if err := db.AutoMigrate(&models.User{}, &models.Post{}, &models.Comment{}, &models.Tag{}); err != nil {
		log.Fatalf("failed to run migrations: %v", err)
	}

	app := fiber.New(fiber.Config{
		AppName: "blog_api",
	})

	app.Use(logger.New())
	app.Use(recover.New())
	app.Use(cors.New())

	app.Get("/health", func(c *fiber.Ctx) error {
		return c.JSON(fiber.Map{"status": "healthy"})
	})

	routes.Register(app, db)

	port := os.Getenv("PORT")
	if port == "" {
		port = "8000"
	}

	log.Fatal(app.Listen(":" + port))
}
