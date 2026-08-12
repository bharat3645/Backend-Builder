package handlers

import (
	"github.com/gofiber/fiber/v2"
	"golang.org/x/crypto/bcrypt"
	"gorm.io/gorm"

	"github.com/backend-builder/blog-api/models"
)

// ListUser returns every User record.
func ListUser(db *gorm.DB) fiber.Handler {
	return func(c *fiber.Ctx) error {
		var items []models.User
		if err := db.Find(&items).Error; err != nil {
			return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{"error": err.Error()})
		}
		return c.JSON(items)
	}
}

// GetUser returns a single User by id.
func GetUser(db *gorm.DB) fiber.Handler {
	return func(c *fiber.Ctx) error {
		var item models.User
		if err := db.First(&item, "id = ?", c.Params("id")).Error; err != nil {
			return c.Status(fiber.StatusNotFound).JSON(fiber.Map{"error": "not found"})
		}
		return c.JSON(item)
	}
}

// CreateUser creates a new User.
func CreateUser(db *gorm.DB) fiber.Handler {
	return func(c *fiber.Ctx) error {
		var item models.User
		if err := c.BodyParser(&item); err != nil {
			return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{"error": err.Error()})
		}
		if item.Password != "" {
			hashed, err := bcrypt.GenerateFromPassword([]byte(item.Password), bcrypt.DefaultCost)
			if err != nil {
				return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{"error": "failed to hash password"})
			}
			item.Password = string(hashed)
		}
		if err := db.Create(&item).Error; err != nil {
			return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{"error": err.Error()})
		}
		return c.Status(fiber.StatusCreated).JSON(item)
	}
}

// UpdateUser updates an existing User.
func UpdateUser(db *gorm.DB) fiber.Handler {
	return func(c *fiber.Ctx) error {
		var item models.User
		if err := db.First(&item, "id = ?", c.Params("id")).Error; err != nil {
			return c.Status(fiber.StatusNotFound).JSON(fiber.Map{"error": "not found"})
		}
		var updates models.User
		if err := c.BodyParser(&updates); err != nil {
			return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{"error": err.Error()})
		}
		if err := db.Model(&item).Updates(updates).Error; err != nil {
			return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{"error": err.Error()})
		}
		return c.JSON(item)
	}
}

// DeleteUser deletes a User by id.
func DeleteUser(db *gorm.DB) fiber.Handler {
	return func(c *fiber.Ctx) error {
		if err := db.Delete(&models.User{}, "id = ?", c.Params("id")).Error; err != nil {
			return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{"error": err.Error()})
		}
		return c.SendStatus(fiber.StatusNoContent)
	}
}

// ListPost returns every Post record.
func ListPost(db *gorm.DB) fiber.Handler {
	return func(c *fiber.Ctx) error {
		var items []models.Post
		if err := db.Find(&items).Error; err != nil {
			return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{"error": err.Error()})
		}
		return c.JSON(items)
	}
}

// GetPost returns a single Post by id.
func GetPost(db *gorm.DB) fiber.Handler {
	return func(c *fiber.Ctx) error {
		var item models.Post
		if err := db.First(&item, "id = ?", c.Params("id")).Error; err != nil {
			return c.Status(fiber.StatusNotFound).JSON(fiber.Map{"error": "not found"})
		}
		return c.JSON(item)
	}
}

// CreatePost creates a new Post.
func CreatePost(db *gorm.DB) fiber.Handler {
	return func(c *fiber.Ctx) error {
		var item models.Post
		if err := c.BodyParser(&item); err != nil {
			return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{"error": err.Error()})
		}
		if err := db.Create(&item).Error; err != nil {
			return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{"error": err.Error()})
		}
		return c.Status(fiber.StatusCreated).JSON(item)
	}
}

// UpdatePost updates an existing Post.
func UpdatePost(db *gorm.DB) fiber.Handler {
	return func(c *fiber.Ctx) error {
		var item models.Post
		if err := db.First(&item, "id = ?", c.Params("id")).Error; err != nil {
			return c.Status(fiber.StatusNotFound).JSON(fiber.Map{"error": "not found"})
		}
		var updates models.Post
		if err := c.BodyParser(&updates); err != nil {
			return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{"error": err.Error()})
		}
		if err := db.Model(&item).Updates(updates).Error; err != nil {
			return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{"error": err.Error()})
		}
		return c.JSON(item)
	}
}

// DeletePost deletes a Post by id.
func DeletePost(db *gorm.DB) fiber.Handler {
	return func(c *fiber.Ctx) error {
		if err := db.Delete(&models.Post{}, "id = ?", c.Params("id")).Error; err != nil {
			return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{"error": err.Error()})
		}
		return c.SendStatus(fiber.StatusNoContent)
	}
}

// ListComment returns every Comment record.
func ListComment(db *gorm.DB) fiber.Handler {
	return func(c *fiber.Ctx) error {
		var items []models.Comment
		if err := db.Find(&items).Error; err != nil {
			return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{"error": err.Error()})
		}
		return c.JSON(items)
	}
}

// GetComment returns a single Comment by id.
func GetComment(db *gorm.DB) fiber.Handler {
	return func(c *fiber.Ctx) error {
		var item models.Comment
		if err := db.First(&item, "id = ?", c.Params("id")).Error; err != nil {
			return c.Status(fiber.StatusNotFound).JSON(fiber.Map{"error": "not found"})
		}
		return c.JSON(item)
	}
}

// CreateComment creates a new Comment.
func CreateComment(db *gorm.DB) fiber.Handler {
	return func(c *fiber.Ctx) error {
		var item models.Comment
		if err := c.BodyParser(&item); err != nil {
			return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{"error": err.Error()})
		}
		if err := db.Create(&item).Error; err != nil {
			return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{"error": err.Error()})
		}
		return c.Status(fiber.StatusCreated).JSON(item)
	}
}

// UpdateComment updates an existing Comment.
func UpdateComment(db *gorm.DB) fiber.Handler {
	return func(c *fiber.Ctx) error {
		var item models.Comment
		if err := db.First(&item, "id = ?", c.Params("id")).Error; err != nil {
			return c.Status(fiber.StatusNotFound).JSON(fiber.Map{"error": "not found"})
		}
		var updates models.Comment
		if err := c.BodyParser(&updates); err != nil {
			return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{"error": err.Error()})
		}
		if err := db.Model(&item).Updates(updates).Error; err != nil {
			return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{"error": err.Error()})
		}
		return c.JSON(item)
	}
}

// DeleteComment deletes a Comment by id.
func DeleteComment(db *gorm.DB) fiber.Handler {
	return func(c *fiber.Ctx) error {
		if err := db.Delete(&models.Comment{}, "id = ?", c.Params("id")).Error; err != nil {
			return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{"error": err.Error()})
		}
		return c.SendStatus(fiber.StatusNoContent)
	}
}

// ListTag returns every Tag record.
func ListTag(db *gorm.DB) fiber.Handler {
	return func(c *fiber.Ctx) error {
		var items []models.Tag
		if err := db.Find(&items).Error; err != nil {
			return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{"error": err.Error()})
		}
		return c.JSON(items)
	}
}

// GetTag returns a single Tag by id.
func GetTag(db *gorm.DB) fiber.Handler {
	return func(c *fiber.Ctx) error {
		var item models.Tag
		if err := db.First(&item, "id = ?", c.Params("id")).Error; err != nil {
			return c.Status(fiber.StatusNotFound).JSON(fiber.Map{"error": "not found"})
		}
		return c.JSON(item)
	}
}

// CreateTag creates a new Tag.
func CreateTag(db *gorm.DB) fiber.Handler {
	return func(c *fiber.Ctx) error {
		var item models.Tag
		if err := c.BodyParser(&item); err != nil {
			return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{"error": err.Error()})
		}
		if err := db.Create(&item).Error; err != nil {
			return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{"error": err.Error()})
		}
		return c.Status(fiber.StatusCreated).JSON(item)
	}
}

// UpdateTag updates an existing Tag.
func UpdateTag(db *gorm.DB) fiber.Handler {
	return func(c *fiber.Ctx) error {
		var item models.Tag
		if err := db.First(&item, "id = ?", c.Params("id")).Error; err != nil {
			return c.Status(fiber.StatusNotFound).JSON(fiber.Map{"error": "not found"})
		}
		var updates models.Tag
		if err := c.BodyParser(&updates); err != nil {
			return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{"error": err.Error()})
		}
		if err := db.Model(&item).Updates(updates).Error; err != nil {
			return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{"error": err.Error()})
		}
		return c.JSON(item)
	}
}

// DeleteTag deletes a Tag by id.
func DeleteTag(db *gorm.DB) fiber.Handler {
	return func(c *fiber.Ctx) error {
		if err := db.Delete(&models.Tag{}, "id = ?", c.Params("id")).Error; err != nil {
			return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{"error": err.Error()})
		}
		return c.SendStatus(fiber.StatusNoContent)
	}
}

