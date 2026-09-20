# Backend - Architecture

This project follows the principles of clean architecture to achieve a well-structured, maintainable, and testable codebase. The application is divided into four main layers:

1. **Domain Layer**
2. **Application Layer**
3. **Infrastructure Layer**
4. **Presentation Layer**

## Domain Layer

The domain layer contains the core business logic and domain entities of the application. It is independent of any external dependencies or frameworks.

### Components

- **Entities**: Represent the core domain objects and their behavior (e.g., `ecole`, `admin`,`Prof` , `exam` ...).
- **Domain Events**: Events that occur within the domain (e.g., `UserRegistered`...).
- **Aggregates**: Cluster roots that combine multiple entities and value objects into a single unit of consistency.
- **Domain Services**: Services that encapsulate domain logic and operations that don't belong to a specific entity or value object.
- **Repositories**: Interfaces that define the contract for persisting and retrieving entities from a data source.
- **Specifications**: Reusable rules or predicates that can be applied to entities or value objects.

## Application Layer

The application layer orchestrates the flow between the domain layer and the infrastructure layer. It handles use cases and application-level concerns.

### Components

- **Use Cases**: Classes that encapsulate the application's business logic and orchestrate the flow between the domain layer and the infrastructure layer.
- **Application Services**: Services that handle application-level concerns, such as transactions, security, or logging.
- **DTO (Data Transfer Object)**: Plain objects used for transferring data between layers, typically between the application layer and the presentation layer.

## Infrastructure Layer

The infrastructure layer handles external dependencies, such as databases, external services, and third-party libraries.

### Components

- **Persistence**: Repositories that implement the interfaces defined in the domain layer (e.g., database repositories, file repositories, remote API repositories).
- **External Services**: Classes that interact with external services or systems (e.g., email providers, payment gateways, third-party APIs).
- **Messaging**: Components for sending and receiving messages (e.g., message queues, event buses).
- **Caching**: Components for caching data (e.g., in-memory caches, distributed caches).
- **Configuration**: Components for managing application configuration (e.g., environment variables, configuration files).
- **Logging**: Components for logging application events and errors.
- **Migrations**: Scripts or classes for managing database schema changes or data migrations.

## Presentation Layer

The presentation layer handles HTTP requests and responses, and typically delegates work to the application layer.

### Components

- **Controllers**: Handle HTTP requests and responses, and typically delegate work to the application layer.
- **Views**: Templates or components for rendering the user interface (if applicable).
- **Mappers**: Classes that map between DTOs and domain entities or vice versa.
- **Filters**: Classes that handle exceptions and error handling in the presentation layer.
- **Guards**: Classes that handle authentication and authorization in the presentation layer.
- **Interceptors**: Classes that intercept and modify requests or responses in the presentation layer.
- **Pipes**: Classes that handle data validation and transformation for incoming requests.

## Benefits of Clean Architecture

By following the principles of clean architecture, this project achieves several benefits:

- **Separation of Concerns**: Each layer has a specific responsibility, promoting code organization and maintainability.
- **Testability**: The separation of layers and the use of interfaces facilitate unit testing and mockability.
- **Flexibility**: The infrastructure layer can be easily swapped out without affecting the core domain logic.
- **Scalability**: The architecture supports the growth and evolution of the application by keeping the core domain logic independent of external concerns.

This documentation provides an overview of the clean architecture implementation in this NestJS project. For more detailed information check the [architecture](docs/architecture/) folder.
