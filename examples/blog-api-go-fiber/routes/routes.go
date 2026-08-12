package routes

import (
	"github.com/gofiber/fiber/v2"
	"gorm.io/gorm"

	"github.com/infranest/blog-api/handlers"
)

// Register wires up REST routes for every model in the DSL spec.
func Register(app *fiber.App, db *gorm.DB) {
	api := app.Group("/api/v1")

	api.Get("/comments", handlers.ListComment(db))
	api.Post("/comments", handlers.CreateComment(db))
	api.Get("/comments/:id", handlers.GetComment(db))
	api.Put("/comments/:id", handlers.UpdateComment(db))
	api.Delete("/comments/:id", handlers.DeleteComment(db))

	api.Get("/posts", handlers.ListPost(db))
	api.Post("/posts", handlers.CreatePost(db))
	api.Get("/posts/:id", handlers.GetPost(db))
	api.Put("/posts/:id", handlers.UpdatePost(db))
	api.Delete("/posts/:id", handlers.DeletePost(db))

	api.Get("/tags", handlers.ListTag(db))
	api.Post("/tags", handlers.CreateTag(db))
	api.Get("/tags/:id", handlers.GetTag(db))
	api.Put("/tags/:id", handlers.UpdateTag(db))
	api.Delete("/tags/:id", handlers.DeleteTag(db))

	api.Get("/users", handlers.ListUser(db))
	api.Post("/users", handlers.CreateUser(db))
	api.Get("/users/:id", handlers.GetUser(db))
	api.Put("/users/:id", handlers.UpdateUser(db))
	api.Delete("/users/:id", handlers.DeleteUser(db))

}
