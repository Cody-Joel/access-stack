FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src

COPY OnnxInference.csproj .
RUN dotnet restore

COPY . .
RUN dotnet build -c Release -o /app/build

FROM mcr.microsoft.com/dotnet/runtime:8.0
WORKDIR /app

COPY --from=build /app/build .
COPY models ./models

ENTRYPOINT ["dotnet", "OnnxInference.dll"]
